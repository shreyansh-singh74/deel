"""Misspelling normalization map for common mistakes."""
from typing import Optional, Dict


# Misspelling map for observed mistakes in the dataset
MISSPELLING_MAP: Dict[str, str] = {
    "talor": "taylor",
    "gonzal ez": "gonzalez",
    "rodri guez": "rodriguez",
    "leedsfor": "leeds for",  # Glued word
    "brookers": "brooks",  # Common typo
    "matthewbrooks": "matthew brooks",  # Glued compound name
}


def normalize_misspelling(text: str) -> str:
    """
    Normalize common misspellings in text.
    
    Args:
        text: Text that may contain misspellings
        
    Returns:
        Corrected text or original if no correction found
    """
    text_lower = text.lower().strip()
    
    # Try exact match first
    if text_lower in MISSPELLING_MAP:
        return MISSPELLING_MAP[text_lower]
    
    # Try partial matches (for glued words)
    for misspelling, correction in MISSPELLING_MAP.items():
        if misspelling in text_lower:
            # Replace the misspelling with correction
            return text_lower.replace(misspelling, correction)
    
    return text

