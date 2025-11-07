"""Observability and logging for the matching pipeline."""
import json
import os
import hashlib
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.config.settings import config


class RequestLogger:
    """Structured logging for matching requests."""
    
    def __init__(self, log_dir: str = "logs", debug_mode: bool = False):
        """
        Initialize RequestLogger.
        
        Args:
            log_dir: Directory for log files
            debug_mode: Enable debug logging
        """
        self.log_dir = log_dir
        self.debug_mode = debug_mode
        os.makedirs(log_dir, exist_ok=True)
        
        # Metrics counters
        self.metrics = {
            'fuzzy_matches': 0,
            'embedding_matches': 0,
            'no_matches': 0,
            'errors': 0
        }
    
    def log_request(
        self,
        transaction_id: str,
        candidates: List[str],
        method: str,
        scores: List[float],
        duration_ms: float,
        anchor: Optional[str] = None,
        penalty_applied: Optional[bool] = None,
        soft_cleaned: Optional[str] = None,
        hard_cleaned: Optional[str] = None
    ):
        """
        Log a matching request.
        
        Args:
            transaction_id: Transaction ID
            candidates: List of extracted candidates
            method: Matching method used ("fuzzy" or "embedding")
            scores: List of match scores
            duration_ms: Request duration in milliseconds
            anchor: Anchor used (optional)
            penalty_applied: Whether penalty was applied (optional)
            soft_cleaned: Soft-cleaned text (optional, hashed if not debug)
            hard_cleaned: Hard-cleaned text (optional, hashed if not debug)
        """
        # Hash long strings if not in debug mode
        if soft_cleaned and not self.debug_mode:
            soft_cleaned = self._hash_string(soft_cleaned)
        if hard_cleaned and not self.debug_mode:
            hard_cleaned = self._hash_string(hard_cleaned)
        
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'transaction_id': transaction_id,
            'method': method,
            'candidates': candidates,
            'top_score': max(scores) if scores else 0.0,
            'num_matches': len(scores),
            'duration_ms': duration_ms,
            'anchor': anchor,
            'penalty_applied': penalty_applied,
            'soft_cleaned': soft_cleaned,
            'hard_cleaned': hard_cleaned
        }
        
        # Write to JSONL file
        log_file = os.path.join(self.log_dir, f"matching_{datetime.utcnow().strftime('%Y%m%d')}.jsonl")
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        # Update metrics
        if method == 'fuzzy':
            self.metrics['fuzzy_matches'] += 1
        elif method == 'embedding':
            self.metrics['embedding_matches'] += 1
        
        if not scores:
            self.metrics['no_matches'] += 1
    
    def get_debug_info(
        self,
        transaction_id: str,
        soft_cleaned: str,
        hard_cleaned: str,
        candidates: List[Any],
        variants: Dict[str, List[str]],
        fuzzy_scores: Optional[List[Dict[str, Any]]] = None,
        embedding_scores: Optional[List[Dict[str, Any]]] = None,
        final_matches: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get debug information for a request (only if debug mode enabled).
        
        Args:
            transaction_id: Transaction ID
            soft_cleaned: Soft-cleaned text
            hard_cleaned: Hard-cleaned text
            candidates: List of candidate objects
            variants: Dictionary mapping candidates to variants
            fuzzy_scores: Fuzzy matching scores (optional)
            embedding_scores: Embedding matching scores (optional)
            final_matches: Final matches (optional)
            
        Returns:
            Debug information dictionary
        """
        if not self.debug_mode:
            return {}
        
        return {
            'transaction_id': transaction_id,
            'soft_cleaned': soft_cleaned,
            'hard_cleaned': hard_cleaned,
            'candidates': [
                {
                    'text': c.text if hasattr(c, 'text') else str(c),
                    'anchor': c.anchor if hasattr(c, 'anchor') else None
                }
                for c in candidates
            ],
            'variants': variants,
            'fuzzy_scores': fuzzy_scores,
            'embedding_scores': embedding_scores,
            'final_matches': final_matches
        }
    
    def _hash_string(self, text: str, max_length: int = 50) -> str:
        """
        Hash a string for logging (privacy-preserving).
        
        Args:
            text: Text to hash
            max_length: Maximum length to show before hashing
            
        Returns:
            Hashed or truncated string
        """
        if len(text) <= max_length:
            return text
        hash_obj = hashlib.md5(text.encode())
        return f"{text[:max_length]}...{hash_obj.hexdigest()[:8]}"
    
    def get_metrics(self) -> Dict[str, int]:
        """
        Get current metrics.
        
        Returns:
            Dictionary of metrics
        """
        return self.metrics.copy()

