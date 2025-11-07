"""Fuzzy matching for candidate-user pairs."""
from typing import List, Dict, Any, Optional
from rapidfuzz import fuzz

from app.config.settings import Config


class FuzzyMatcher:
    """Fuzzy matching with bonuses and penalties."""
    
    def __init__(self, config: Config):
        """
        Initialize FuzzyMatcher.
        
        Args:
            config: Configuration object
        """
        self.config = config
    
    def fuzzy_match(
        self,
        candidate_variants: List[str],
        preprocessed_users: List[Dict[str, Any]],
        threshold: Optional[float] = None,
        description: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Match candidate variants against preprocessed users using fuzzy matching.
        
        Args:
            candidate_variants: List of candidate variant strings
            preprocessed_users: List of preprocessed user records
            threshold: Minimum score threshold (defaults to config.FUZZY_ACCEPT)
            description: Original description for context (for CC detection)
            
        Returns:
            List of match dictionaries with user info and scores
        """
        if threshold is None:
            threshold = self.config.FUZZY_ACCEPT
        
        matches = []
        
        for candidate_variant in candidate_variants:
            if not candidate_variant:
                continue
            
            for user in preprocessed_users:
                user_name = user.get('name_strip_accents', '')
                if not user_name:
                    continue
                
                # Compute base fuzzy score
                base_score = self._compute_base_score(candidate_variant, user_name)
                
                # Apply bonuses/penalties
                final_score = self._apply_bonuses_penalties(
                    base_score,
                    candidate_variant,
                    user,
                    description
                )
                
                # Cap at 100
                final_score = min(100.0, max(0.0, final_score))
                
                # Only add if above threshold
                if final_score >= threshold:
                    matches.append({
                        'user_id': user['id'],
                        'user_name': user['name_raw'],
                        'score': final_score,
                        'candidate': candidate_variant,
                        'base_score': base_score
                    })
        
        # Sort by score descending
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        return matches
    
    def _compute_base_score(self, candidate: str, user_name: str) -> float:
        """
        Compute base fuzzy score using multiple metrics.
        
        Args:
            candidate: Candidate variant string
            user_name: User normalized name
            
        Returns:
            Maximum score from different fuzzy metrics
        """
        # Use multiple fuzzy metrics and take the max
        scores = [
            fuzz.token_sort_ratio(candidate, user_name),
            fuzz.partial_ratio(candidate, user_name),
            fuzz.ratio(candidate, user_name),
            fuzz.token_set_ratio(candidate, user_name),
        ]
        
        # Also try jaro-winkler if available (through WRatio which includes it)
        try:
            scores.append(fuzz.WRatio(candidate, user_name))
        except:
            pass
        
        return max(scores)
    
    def _apply_bonuses_penalties(
        self,
        base_score: float,
        candidate: str,
        user: Dict[str, Any],
        description: str
    ) -> float:
        """
        Apply bonuses and penalties to base score.
        
        Bonuses:
        - +5 first-name overlap
        - +5 last-name overlap
        - +3 initials match
        
        Penalties:
        - -8 if candidate in "cc ..." region
        - -5 if text contains "err#"
        
        Args:
            base_score: Base fuzzy score
            candidate: Candidate variant string
            user: Preprocessed user record
            description: Original description for context
            
        Returns:
            Adjusted score
        """
        score = base_score
        
        # Tokenize candidate
        candidate_tokens = candidate.lower().split()
        user_tokens = user.get('tokens', [])
        
        if not user_tokens:
            return score
        
        # First name overlap bonus
        if candidate_tokens and user_tokens:
            if candidate_tokens[0].lower() == user_tokens[0].lower():
                score += self.config.FIRST_NAME_OVERLAP
        
        # Last name overlap bonus
        if len(candidate_tokens) > 1 and len(user_tokens) > 1:
            if candidate_tokens[-1].lower() == user_tokens[-1].lower():
                score += self.config.LAST_NAME_OVERLAP
        
        # Initials match bonus
        user_initials = user.get('initials', '').lower()
        if user_initials:
            candidate_initials = ''.join(t[0] for t in candidate_tokens if t).lower()
            if candidate_initials == user_initials:
                score += self.config.INITIALS_MATCH
        
        # CC penalty (if candidate appears after "cc" in description)
        description_lower = description.lower()
        candidate_lower = candidate.lower()
        if 'cc' in description_lower:
            # Find position of "cc" and candidate
            cc_pos = description_lower.find('cc')
            candidate_pos = description_lower.find(candidate_lower)
            if candidate_pos > cc_pos and candidate_pos < cc_pos + 100:  # Within 100 chars after "cc"
                score += self.config.CC_PENALTY
        
        # ERR# penalty
        if 'err#' in description_lower or 'err #' in description_lower:
            # If candidate is near error markers, apply penalty
            if 'err' in description_lower.lower():
                # Simple heuristic: if description has errors, slight penalty
                score += self.config.ERR_PENALTY
        
        return score

