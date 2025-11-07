"""Disambiguation logic for multi-candidate and multi-user collisions."""
import re
from typing import List, Dict, Any
from app.matching.candidate_extractor import Candidate

from app.config.settings import Config


class Disambiguator:
    """Disambiguate matches when multiple candidates or users are close."""
    
    def __init__(self, config: Config):
        """
        Initialize Disambiguator.
        
        Args:
            config: Configuration object
        """
        self.config = config
    
    def disambiguate(
        self,
        matches: List[Dict[str, Any]],
        candidates: List[Candidate],
        description: str
    ) -> List[Dict[str, Any]]:
        """
        Disambiguate matches by applying anchor bonuses and penalties.
        
        Args:
            matches: List of match dictionaries
            candidates: List of candidate objects with anchor metadata
            description: Original description for context
            
        Returns:
            Disambiguated and ranked matches
        """
        if not matches:
            return []
        
        # Create candidate lookup by text
        candidate_lookup = {c.text.lower(): c for c in candidates}
        
        # Apply anchor bonus to matches from primary anchor
        primary_anchor = self._get_primary_anchor(candidates)
        
        for match in matches:
            candidate_text = match.get('candidate', '').lower()
            candidate = candidate_lookup.get(candidate_text)
            
            if candidate:
                # Apply anchor bonus if matches primary anchor
                if candidate.anchor == primary_anchor:
                    match['score'] += self.config.ANCHOR_BONUS
                    match['anchor_bonus_applied'] = True
                
                # Apply CC penalty if in CC region
                if self._is_in_cc_region(candidate, description):
                    match['score'] += self.config.CC_PENALTY
                    match['cc_penalty_applied'] = True
        
        # Prefer exact 3-token matches over 2-token partials
        matches = self._prefer_compound_names(matches)
        
        # Cap scores at 100
        for match in matches:
            match['score'] = min(100.0, max(0.0, match['score']))
        
        # Sort by score descending, then by user_id for stability
        matches.sort(key=lambda x: (x['score'], x['user_id']), reverse=True)
        
        return matches
    
    def _get_primary_anchor(self, candidates: List[Candidate]) -> str:
        """
        Get the primary anchor type from candidates.
        
        Priority: from > ref > for_deel > fallback
        
        Args:
            candidates: List of candidate objects
            
        Returns:
            Primary anchor string
        """
        if not candidates:
            return 'fallback'
        
        # Find highest priority anchor
        anchor_priority = {'from': 3, 'ref': 2, 'for_deel': 1, 'fallback': 0}
        primary = max(candidates, key=lambda c: anchor_priority.get(c.anchor, 0))
        return primary.anchor
    
    def _is_in_cc_region(self, candidate: Candidate, description: str) -> bool:
        """
        Check if candidate is in a CC (carbon copy) region.
        
        Args:
            candidate: Candidate object
            description: Original description
            
        Returns:
            True if candidate appears after "cc" in description
        """
        description_lower = description.lower()
        candidate_lower = candidate.text.lower()
        
        # Find "cc" position
        cc_positions = []
        for match in re.finditer(r'\bcc\b', description_lower):
            cc_positions.append(match.start())
        
        if not cc_positions:
            return False
        
        # Find candidate position in original description
        # Since we're working with cleaned text, we'll use a heuristic
        # Check if "cc" appears before the candidate text
        for cc_pos in cc_positions:
            # Look for candidate text after "cc"
            candidate_search = description_lower[cc_pos:cc_pos + 200]  # Within 200 chars
            if candidate_lower in candidate_search:
                return True
        
        return False
    
    def _prefer_compound_names(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prefer exact 3-token matches over 2-token partials.
        
        Args:
            matches: List of match dictionaries
            
        Returns:
            Matches with adjusted scores for compound names
        """
        # Group matches by user_id to compare token counts
        user_matches = {}
        for match in matches:
            user_id = match['user_id']
            if user_id not in user_matches:
                user_matches[user_id] = []
            user_matches[user_id].append(match)
        
        # For each user, prefer matches with more tokens if both exceed threshold
        for user_id, user_match_list in user_matches.items():
            if len(user_match_list) > 1:
                # Sort by token count in candidate
                user_match_list.sort(
                    key=lambda m: len(m.get('candidate', '').split()),
                    reverse=True
                )
                
                # If top match has 3+ tokens and others have 2, boost the 3+ token match
                top_match = user_match_list[0]
                top_tokens = len(top_match.get('candidate', '').split())
                
                if top_tokens >= 3:
                    for other_match in user_match_list[1:]:
                        other_tokens = len(other_match.get('candidate', '').split())
                        if other_tokens == 2 and other_match['score'] >= self.config.FUZZY_ACCEPT:
                            # Slight boost for compound name
                            top_match['score'] += 2
        
        return matches

