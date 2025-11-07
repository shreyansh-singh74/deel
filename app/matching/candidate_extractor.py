"""Candidate name extraction from transaction descriptions."""
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from app.config.settings import config


@dataclass
class Candidate:
    """Candidate name with metadata."""
    text: str
    anchor: str  # 'from', 'ref', 'for_deel', or 'fallback'
    start_pos: int
    end_pos: int
    priority: int  # Higher = better (from=3, ref=2, for_deel=1, fallback=0)


class CandidateExtractor:
    """Extract candidate names from transaction descriptions."""
    
    # Boilerplate words to filter out
    BOILERPLATE_WORDS = {
        'from', 'for', 'deel', 'payment', 'transfer', 'received', 
        'request', 'credit', 'debit', 'to', 'cntr', 'wise', 'test'
    }
    
    def extract_candidates(
        self, 
        soft_cleaned_text: str, 
        max_candidates: Optional[int] = None
    ) -> List[Candidate]:
        """
        Extract candidate names from soft-cleaned text.
        
        Args:
            soft_cleaned_text: Soft-cleaned description text
            max_candidates: Maximum number of candidates to return
            
        Returns:
            List of Candidate objects with anchor metadata
        """
        if max_candidates is None:
            max_candidates = config.MAX_CANDIDATES
        
        candidates = []
        
        # Extract from different anchor patterns
        candidates.extend(self._extract_after_from(soft_cleaned_text))
        candidates.extend(self._extract_after_ref(soft_cleaned_text))
        candidates.extend(self._extract_before_for_deel(soft_cleaned_text))
        
        # If no candidates found, use fallback windows
        if not candidates:
            candidates.extend(self._fallback_windows(soft_cleaned_text))
        
        # Post-filter and prioritize
        candidates = self._post_filter_candidates(candidates, soft_cleaned_text)
        
        # Sort by priority and take top candidates
        candidates.sort(key=lambda c: (c.priority, -len(c.text)), reverse=True)
        
        # Remove duplicates (same text)
        seen_texts = set()
        unique_candidates = []
        for candidate in candidates:
            text_normalized = candidate.text.lower().strip()
            if text_normalized not in seen_texts and text_normalized:
                seen_texts.add(text_normalized)
                unique_candidates.append(candidate)
                if len(unique_candidates) >= max_candidates:
                    break
        
        return unique_candidates
    
    def _extract_after_from(self, text: str) -> List[Candidate]:
        """Extract name after 'from' anchor."""
        candidates = []
        # Pattern: "from <name>" until "for", comma, or end
        pattern = r'\bfrom\s+([^,]+?)(?:\s+for\b|,|$)'
        for match in re.finditer(pattern, text, re.IGNORECASE):
            name_text = match.group(1).strip()
            if self._is_valid_candidate(name_text):
                candidates.append(Candidate(
                    text=name_text,
                    anchor='from',
                    start_pos=match.start(1),
                    end_pos=match.end(1),
                    priority=3
                ))
        return candidates
    
    def _extract_after_ref(self, text: str) -> List[Candidate]:
        """Extract name after 'ref:' anchor."""
        candidates = []
        # Pattern: "ref: <name>" until comma/end/cntr/for/and/cc
        pattern = r'\bref\s*:\s*([^,]+?)(?:\s+(?:cntr|for|and|cc)\b|,|$)'
        for match in re.finditer(pattern, text, re.IGNORECASE):
            name_text = match.group(1).strip()
            if self._is_valid_candidate(name_text):
                candidates.append(Candidate(
                    text=name_text,
                    anchor='ref',
                    start_pos=match.start(1),
                    end_pos=match.end(1),
                    priority=2
                ))
        return candidates
    
    def _extract_before_for_deel(self, text: str) -> List[Candidate]:
        """Extract name before 'for deel' anchor."""
        candidates = []
        # Pattern: "<name> for deel"
        pattern = r'(.+?)\s+for\s+deel\b'
        for match in re.finditer(pattern, text, re.IGNORECASE):
            # Get the text before "for deel"
            before_text = match.group(1).strip()
            # Try to extract just the name part (last 2-4 words before "for deel")
            words = before_text.split()
            if len(words) >= 2:
                # Take last 2-4 words as potential name
                name_words = words[-4:] if len(words) >= 4 else words
                name_text = ' '.join(name_words)
                if self._is_valid_candidate(name_text):
                    candidates.append(Candidate(
                        text=name_text,
                        anchor='for_deel',
                        start_pos=match.start(1),
                        end_pos=match.end(1),
                        priority=1
                    ))
        return candidates
    
    def _fallback_windows(self, text: str) -> List[Candidate]:
        """Fallback: sliding windows of 2-4 tokens with ≥2 alphabetic tokens."""
        candidates = []
        words = text.split()
        
        if len(words) < 2:
            return candidates
        
        # Try windows of size 2, 3, and 4
        for window_size in [2, 3, 4]:
            for i in range(len(words) - window_size + 1):
                window = words[i:i + window_size]
                window_text = ' '.join(window)
                
                # Check if has at least 2 alphabetic tokens
                alpha_count = sum(1 for w in window if re.search(r'[a-z]', w, re.IGNORECASE))
                if alpha_count >= 2 and self._is_valid_candidate(window_text):
                    candidates.append(Candidate(
                        text=window_text,
                        anchor='fallback',
                        start_pos=i,
                        end_pos=i + window_size,
                        priority=0
                    ))
        
        return candidates
    
    def _is_valid_candidate(self, text: str) -> bool:
        """Check if candidate text is valid (not just boilerplate)."""
        if not text or len(text.strip()) < 2:
            return False
        
        # Check if it's all boilerplate
        words = text.lower().split()
        if all(word in self.BOILERPLATE_WORDS for word in words):
            return False
        
        # Check token count (prefer 2-4 words)
        if len(words) < 1 or len(words) > 6:
            return False
        
        # Should contain at least some alphabetic characters
        if not re.search(r'[a-z]', text, re.IGNORECASE):
            return False
        
        return True
    
    def _post_filter_candidates(
        self, 
        candidates: List[Candidate], 
        text: str
    ) -> List[Candidate]:
        """Post-filter candidates: trim punctuation, prefer 2-4 tokens."""
        filtered = []
        for candidate in candidates:
            # Trim surrounding punctuation
            cleaned = candidate.text.strip('.,;:!?()-[]{}"\'').strip()
            if not cleaned:
                continue
            
            # Prefer 2-4 words
            words = cleaned.split()
            if len(words) < 1 or len(words) > 6:
                continue
            
            # Update candidate text
            candidate.text = cleaned
            filtered.append(candidate)
        
        return filtered

