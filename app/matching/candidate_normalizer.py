"""Candidate normalization and variant generation."""
import re
from typing import List, Set, Optional
from unidecode import unidecode

from app.config.settings import config
from app.matching.transliteration_map import get_transliteration, has_non_latin_chars
from app.matching.misspelling_map import normalize_misspelling


class CandidateNormalizer:
    """Normalize candidates and generate variants."""
    
    def __init__(self, all_user_tokens: Optional[List[str]] = None):
        """
        Initialize CandidateNormalizer.
        
        Args:
            all_user_tokens: List of all user tokens for glued word detection
        """
        self.all_user_tokens = set(all_user_tokens or [])
        # Create a set of common first/last name tokens for better splitting
        self._build_token_combinations()
    
    def _build_token_combinations(self):
        """Build common token combinations for glued word detection."""
        # This will be populated as we see user tokens
        # For now, we'll use heuristics
        pass
    
    def normalize_candidate(self, candidate: str) -> str:
        """
        Normalize a candidate string.
        
        - Strip diacritics
        - Collapse internal spaces
        - Lowercase
        
        Args:
            candidate: Raw candidate text
            
        Returns:
            Normalized candidate
        """
        if not candidate:
            return ""
        
        # Lowercase
        text = candidate.lower().strip()
        
        # Strip diacritics
        text = unidecode(text)
        
        # Collapse internal spaces
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def generate_variants(
        self, 
        candidate: str, 
        max_variants: Optional[int] = None
    ) -> List[str]:
        """
        Generate variants of a candidate.
        
        Variants:
        - Original order
        - Reversed order (if 2 tokens)
        - Remove single-letter middles
        - Drop numeric tails
        - Apply misspelling correction
        - Transliteration if non-Latin
        
        Args:
            candidate: Normalized candidate text
            max_variants: Maximum number of variants to generate
            
        Returns:
            List of variant strings
        """
        if max_variants is None:
            max_variants = config.MAX_VARIANTS_PER_CANDIDATE
        
        variants = set()
        
        # Normalize first
        normalized = self.normalize_candidate(candidate)
        if not normalized:
            return []
        
        # Apply misspelling correction
        corrected = normalize_misspelling(normalized)
        normalized = corrected
        
        # Handle glued words
        normalized = self._split_glued_words(normalized)
        
        # Original order
        variants.add(normalized)
        
        # Split into tokens
        tokens = normalized.split()
        
        if not tokens:
            return list(variants)
        
        # Reversed order (if exactly 2 tokens)
        if len(tokens) == 2:
            reversed_variant = f"{tokens[1]} {tokens[0]}"
            variants.add(reversed_variant)
        
        # Remove single-letter middles (j, k, jr, etc.)
        if len(tokens) > 2:
            filtered_tokens = [
                t for t in tokens 
                if len(t) > 1 or t.lower() not in ['j', 'k', 'jr', 'sr']
            ]
            if len(filtered_tokens) >= 2:
                variants.add(' '.join(filtered_tokens))
        
        # Drop numeric tails
        for token in tokens:
            # Remove trailing digits
            cleaned_token = re.sub(r'\d+$', '', token)
            if cleaned_token and cleaned_token != token:
                # Rebuild with cleaned token
                new_tokens = [t if t != token else cleaned_token for t in tokens]
                variants.add(' '.join(new_tokens))
        
        # Transliteration if non-Latin
        if has_non_latin_chars(candidate):
            transliterated = get_transliteration(candidate)
            if transliterated:
                variants.add(transliterated.lower())
                # Also try reversed if 2 tokens
                translit_tokens = transliterated.split()
                if len(translit_tokens) == 2:
                    variants.add(f"{translit_tokens[1]} {translit_tokens[0]}")
        
        # Limit variants
        variants_list = list(variants)[:max_variants]
        return variants_list
    
    def _split_glued_words(self, text: str) -> str:
        """
        Split glued/concatenated words using user token dictionary.
        
        Args:
            text: Candidate text that may contain glued words
            
        Returns:
            Text with glued words split
        """
        if not self.all_user_tokens:
            return text
        
        tokens = text.split()
        result_tokens = []
        
        for token in tokens:
            # Try to split if token is long and might be glued
            if len(token) > 6:  # Heuristic: long tokens might be glued
                split = self._try_split_token(token)
                if split:
                    result_tokens.extend(split)
                else:
                    result_tokens.append(token)
            else:
                result_tokens.append(token)
        
        return ' '.join(result_tokens)
    
    def _try_split_token(self, token: str) -> Optional[List[str]]:
        """
        Try to split a token into two parts using user token dictionary.
        
        Args:
            token: Token to split
            
        Returns:
            List of split tokens or None if can't split
        """
        if not self.all_user_tokens:
            return None
        
        # Try splitting at various positions
        for split_pos in range(3, len(token) - 2):
            part1 = token[:split_pos]
            part2 = token[split_pos:]
            
            # Check if both parts are in user tokens
            if part1 in self.all_user_tokens and part2 in self.all_user_tokens:
                return [part1, part2]
            
            # Also try with first letter capitalized (common pattern)
            part1_cap = part1.capitalize()
            part2_cap = part2.capitalize()
            if (part1_cap in self.all_user_tokens or part1 in self.all_user_tokens) and \
               (part2_cap in self.all_user_tokens or part2 in self.all_user_tokens):
                return [part1, part2]
        
        return None

