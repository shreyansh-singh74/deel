"""Hybrid pipeline for matching users to transactions."""
import time
import pandas as pd
from typing import Dict, Any, List, Optional
from sentence_transformers import SentenceTransformer

from app.config.settings import config
from app.preprocessing.text_cleaner import TextCleaner
from app.matching.candidate_extractor import CandidateExtractor, Candidate
from app.matching.candidate_normalizer import CandidateNormalizer
from app.matching.fuzzy_matcher import FuzzyMatcher
from app.matching.embedding_matcher import EmbeddingMatcher
from app.matching.disambiguator import Disambiguator
from app.observability.logger import RequestLogger


def match_users(
    transaction_id: str,
    transactions: pd.DataFrame,
    preprocessed_users: List[Dict[str, Any]],
    embedding_model: SentenceTransformer,
    logger: Optional[RequestLogger] = None
) -> Dict[str, Any]:
    """
    Match users to a transaction using hybrid fuzzy+embedding pipeline.
    
    Args:
        transaction_id: The ID of the transaction to match
        transactions: DataFrame containing transaction data
        preprocessed_users: List of preprocessed user records
        embedding_model: Multilingual embedding model
        logger: Optional request logger
        
    Returns:
        Dictionary with matched users and total count:
        {
            "users": [{"id": "...", "name": "...", "match_metric": 0-100, "method": "fuzzy|embedding"}],
            "total_number_of_matches": N
        }
    """
    start_time = time.time()
    
    # Find the transaction
    transaction = transactions[transactions["id"] == transaction_id]
    if transaction.empty:
        return {"error": "Transaction not found"}
    
    # Get the description
    description = str(transaction.iloc[0]["description"])
    if not description:
        return {
            "users": [],
            "total_number_of_matches": 0
        }
    
    # Initialize components
    text_cleaner = TextCleaner()
    candidate_extractor = CandidateExtractor()
    
    # Get all user tokens for normalizer
    all_user_tokens = []
    for user in preprocessed_users:
        all_user_tokens.extend(user.get('tokens', []))
    candidate_normalizer = CandidateNormalizer(all_user_tokens=all_user_tokens)
    
    fuzzy_matcher = FuzzyMatcher(config)
    embedding_matcher = EmbeddingMatcher(config, embedding_model)
    disambiguator = Disambiguator(config)
    
    # Step 1: Soft clean description
    soft_cleaned = text_cleaner.soft_clean(
        description, 
        max_length=config.MAX_DESCRIPTION_LENGTH
    )
    
    # Step 2: Extract candidates
    candidates = candidate_extractor.extract_candidates(
        soft_cleaned,
        max_candidates=config.MAX_CANDIDATES
    )
    
    # Step 3: If no candidates, use hard clean + fallback windows
    if not candidates:
        hard_cleaned = text_cleaner.hard_clean(
            description,
            max_length=config.MAX_DESCRIPTION_LENGTH
        )
        candidates = candidate_extractor.extract_candidates(
            hard_cleaned,
            max_candidates=config.MAX_CANDIDATES
        )
        # If still no candidates and description is too short/noisy, return empty
        if not candidates:
            tokens = hard_cleaned.split()
            if len(tokens) < 2:
                duration_ms = (time.time() - start_time) * 1000
                if logger:
                    logger.log_request(
                        transaction_id=transaction_id,
                        candidates=[],
                        method="none",
                        scores=[],
                        duration_ms=duration_ms,
                        soft_cleaned=soft_cleaned,
                        hard_cleaned=hard_cleaned
                    )
                return {
                    "users": [],
                    "total_number_of_matches": 0
                }
    
    # Step 4: Normalize candidates & generate variants
    candidate_variants_map = {}
    all_variants = []
    for candidate in candidates:
        normalized = candidate_normalizer.normalize_candidate(candidate.text)
        variants = candidate_normalizer.generate_variants(
            normalized,
            max_variants=config.MAX_VARIANTS_PER_CANDIDATE
        )
        candidate_variants_map[candidate.text] = variants
        all_variants.extend(variants)
    
    # Step 5: Fuzzy match first
    fuzzy_matches = fuzzy_matcher.fuzzy_match(
        all_variants,
        preprocessed_users,
        threshold=config.FUZZY_ACCEPT,
        description=description
    )
    
    method = "fuzzy"
    matches = fuzzy_matches
    top_score = max([m['score'] for m in fuzzy_matches]) if fuzzy_matches else 0.0
    
    # Step 6: If fuzzy weak, try embedding fallback
    if not fuzzy_matches or top_score < config.FUZZY_ACCEPT:
        try:
            embedding_matches = embedding_matcher.embedding_match(
                all_variants,
                preprocessed_users,
                threshold=config.EMB_ACCEPT,
                timeout_ms=config.EMBEDDING_TIMEOUT_MS
            )
            
            if embedding_matches:
                # Check if embedding top score is good enough
                emb_top_score = max([m['cosine_sim'] for m in embedding_matches])
                if emb_top_score >= config.EMB_ACCEPT:
                    method = "embedding"
                    matches = embedding_matches
                    top_score = max([m['score'] for m in embedding_matches])
        except Exception as e:
            # If embedding fails, use fuzzy results (even if below threshold)
            if logger:
                logger.metrics['errors'] += 1
            pass
    
    # Step 7: Disambiguate results
    if matches:
        matches = disambiguator.disambiguate(
            matches,
            candidates,
            description
        )
    else:
        # No matches found - return empty
        duration_ms = (time.time() - start_time) * 1000
        if logger:
            logger.log_request(
                transaction_id=transaction_id,
                candidates=[c.text for c in candidates],
                method=method,
                scores=[],
                duration_ms=duration_ms,
                soft_cleaned=soft_cleaned
            )
        return {
            "users": [],
            "total_number_of_matches": 0
        }
    
    # Step 8: Format output
    top_k = config.get_top_k()
    top_matches = matches[:top_k]
    
    results = []
    for match in top_matches:
        results.append({
            "id": match['user_id'],
            "name": match['user_name'],
            "match_metric": round(match['score'], 2),
            "method": method
        })
    
    # Step 9: Log request
    duration_ms = (time.time() - start_time) * 1000
    if logger:
        scores = [m['score'] for m in top_matches]
        primary_anchor = candidates[0].anchor if candidates else None
        penalty_applied = any(
            m.get('cc_penalty_applied', False) or m.get('anchor_bonus_applied', False)
            for m in top_matches
        )
        logger.log_request(
            transaction_id=transaction_id,
            candidates=[c.text for c in candidates],
            method=method,
            scores=scores,
            duration_ms=duration_ms,
            anchor=primary_anchor,
            penalty_applied=penalty_applied,
            soft_cleaned=soft_cleaned
        )
    
    return {
        "users": results,
        "total_number_of_matches": len(results)
    }
