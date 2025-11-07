"""Embedding-based matching for candidate-user pairs."""
import time
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer

from app.config.settings import Config
from app.matching.transliteration_map import get_transliteration, has_non_latin_chars


class EmbeddingMatcher:
    """Multilingual embedding matching with transliteration."""
    
    def __init__(self, config: Config, embedding_model: SentenceTransformer):
        """
        Initialize EmbeddingMatcher.
        
        Args:
            config: Configuration object
            embedding_model: Pre-loaded multilingual embedding model
        """
        self.config = config
        self.embedding_model = embedding_model
    
    def embedding_match(
        self,
        candidate_variants: List[str],
        preprocessed_users: List[Dict[str, Any]],
        threshold: Optional[float] = None,
        timeout_ms: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Match candidate variants against preprocessed users using embeddings.
        
        Args:
            candidate_variants: List of candidate variant strings
            preprocessed_users: List of preprocessed user records
            threshold: Minimum cosine similarity threshold (defaults to config.EMB_ACCEPT)
            timeout_ms: Maximum time in milliseconds (defaults to config.EMBEDDING_TIMEOUT_MS)
            
        Returns:
            List of match dictionaries with user info and scores (0-100)
        """
        if threshold is None:
            threshold = self.config.EMB_ACCEPT
        
        if timeout_ms is None:
            timeout_ms = self.config.EMBEDDING_TIMEOUT_MS
        
        if not candidate_variants:
            return []
        
        start_time = time.time()
        matches = []
        
        # Get best candidate variant (first one, or try transliteration)
        best_candidate = candidate_variants[0]
        
        # Check if transliteration is needed
        transliterated = None
        if has_non_latin_chars(best_candidate):
            transliterated = get_transliteration(best_candidate)
        
        # Prepare texts to embed
        texts_to_embed = [best_candidate]
        if transliterated and transliterated != best_candidate:
            texts_to_embed.append(transliterated)
        
        # Check timeout before embedding
        elapsed_ms = (time.time() - start_time) * 1000
        if elapsed_ms > timeout_ms:
            return []
        
        try:
            # Embed candidate variants
            candidate_embeddings = self.embedding_model.encode(
                texts_to_embed,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            # Use the best embedding (first one)
            candidate_embedding = candidate_embeddings[0]
            
            # Normalize embeddings for cosine similarity
            candidate_embedding = candidate_embedding / np.linalg.norm(candidate_embedding)
            
            # Compare with all user embeddings
            for user in preprocessed_users:
                user_embedding = user.get('embedding')
                if user_embedding is None:
                    continue
                
                # Check timeout periodically
                elapsed_ms = (time.time() - start_time) * 1000
                if elapsed_ms > timeout_ms:
                    break
                
                # Normalize user embedding
                user_embedding_norm = user_embedding / np.linalg.norm(user_embedding)
                
                # Compute cosine similarity
                cosine_sim = np.dot(candidate_embedding, user_embedding_norm)
                
                # Scale to 0-100 for match_metric
                score = float(cosine_sim * 100.0)
                
                # Only add if above threshold (cosine similarity)
                if cosine_sim >= threshold:
                    matches.append({
                        'user_id': user['id'],
                        'user_name': user['name_raw'],
                        'score': score,
                        'cosine_sim': float(cosine_sim),
                        'candidate': best_candidate
                    })
        
        except Exception as e:
            print(f"Error in embedding matching: {e}")
            return []
        
        # Sort by score descending
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        return matches
    
    def _cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            emb1: First embedding vector
            emb2: Second embedding vector
            
        Returns:
            Cosine similarity (0-1)
        """
        # Normalize
        emb1_norm = emb1 / np.linalg.norm(emb1)
        emb2_norm = emb2 / np.linalg.norm(emb2)
        
        # Dot product
        return float(np.dot(emb1_norm, emb2_norm))

