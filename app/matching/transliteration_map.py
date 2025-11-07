"""Transliteration map for known non-Latin names."""
from typing import Optional, Dict


# Transliteration map for known non-Latin names in the dataset
TRANSLITERATION_MAP: Dict[str, str] = {
    # Chinese names
    "杨陈": "yang chen",
    "陈剑": "jian chen",
    "刘王": "liu wang",
    "李周": "li zhou",
    # Greek names
    "Αλέξανδρος Μπέικερ": "alexander baker",
    "Στέλλα Σάντερς": "stella sanders",
    "Ανδρέας Ροντέελ": "andreas rodeel",
    "Ἄλεξις": "alexis",
    # Hebrew names
    "אֲבִיגַיִל גרין": "avigail green",
}


def get_transliteration(name: str) -> Optional[str]:
    """
    Get transliterated version of a non-Latin name if it exists in the map.
    
    Args:
        name: The original name string
        
    Returns:
        Transliterated string or None if not found
    """
    # Try exact match first
    if name in TRANSLITERATION_MAP:
        return TRANSLITERATION_MAP[name]
    
    # Try case-insensitive match
    name_lower = name.lower().strip()
    for key, value in TRANSLITERATION_MAP.items():
        if key.lower().strip() == name_lower:
            return value
    
    return None


def has_non_latin_chars(text: str) -> bool:
    """
    Check if text contains non-Latin characters.
    
    Args:
        text: Text to check
        
    Returns:
        True if contains non-Latin characters
    """
    for char in text:
        # Check if character is outside ASCII range and not a common punctuation
        if ord(char) > 127 and char not in '.,;:!?-()[]{}':
            return True
    return False

