"""Text cleaning utilities for transaction descriptions."""
import re
import unicodedata
from typing import Optional


class TextCleaner:
    """Clean transaction descriptions for name extraction."""
    
    # Boilerplate tokens to remove in hard clean
    BOILERPLATE_PATTERN = re.compile(
        r'\b(from|for|deel|payment|transfer|received|request|credit|debit|to deel|cntr|wise|test)\b',
        re.IGNORECASE
    )
    
    # ACC//<digits|space|dot> blocks
    ACC_PATTERN = re.compile(r'ACC//[\d\s\.]+', re.IGNORECASE)
    
    @staticmethod
    def soft_clean(text: str, max_length: Optional[int] = None) -> str:
        """
        Soft clean text for candidate extraction.
        
        - NFKC → lowercase
        - Replace digit-lookalikes inside words (0→o, 1→l)
        - Remove ACC//<digits|space|dot> blocks
        - Keep ref: tokens intact
        - Remove symbols to spaces, keep colons
        - Collapse spaces
        
        Args:
            text: Raw description text
            max_length: Maximum length to truncate (optional)
            
        Returns:
            Soft-cleaned text
        """
        if not text:
            return ""
        
        # Unicode normalize (NFKC)
        text = unicodedata.normalize('NFKC', text)
        
        # Lowercase
        text = text.lower()
        
        # Replace digit-lookalikes inside words (0→o, 1→l)
        # Only replace if they're inside word boundaries
        text = re.sub(r'\b0([a-z])', r'o\1', text)
        text = re.sub(r'([a-z])0\b', r'\1o', text)
        text = re.sub(r'\b1([a-z])', r'l\1', text)
        text = re.sub(r'([a-z])1\b', r'\1l', text)
        text = re.sub(r'\b0\b', 'o', text)  # Standalone 0
        text = re.sub(r'\b1\b', 'l', text)  # Standalone 1
        
        # Remove ACC//<digits|space|dot> blocks
        text = TextCleaner.ACC_PATTERN.sub('', text)
        
        # Keep ref: tokens intact - protect them temporarily
        ref_placeholder = " __REF_PLACEHOLDER__ "
        text = re.sub(r'\bref\s*:', ref_placeholder, text, flags=re.IGNORECASE)
        
        # Remove symbols to spaces, but keep colons
        # Replace punctuation except colons and alphanumerics with spaces
        text = re.sub(r'[^\w\s:]', ' ', text)
        
        # Restore ref: tokens
        text = text.replace('__REF_PLACEHOLDER__', 'ref:')
        
        # Collapse spaces
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Truncate if needed
        if max_length and len(text) > max_length:
            text = text[:max_length]
        
        return text
    
    @staticmethod
    def hard_clean(text: str, max_length: Optional[int] = None) -> str:
        """
        Hard clean text for fallback windows.
        
        Soft clean plus remove boilerplate tokens.
        
        Args:
            text: Raw description text
            max_length: Maximum length to truncate (optional)
            
        Returns:
            Hard-cleaned text
        """
        if not text:
            return ""
        
        # Start with soft clean
        text = TextCleaner.soft_clean(text, max_length)
        
        # Remove boilerplate tokens
        text = TextCleaner.BOILERPLATE_PATTERN.sub(' ', text)
        
        # Collapse spaces again
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text

