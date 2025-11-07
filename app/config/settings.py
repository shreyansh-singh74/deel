"""Centralized configuration for the matching pipeline."""
from dataclasses import dataclass
from typing import Tuple


@dataclass
class Config:
    """Configuration class with all thresholds, bonuses, and limits."""
    
    # Thresholds
    FUZZY_ACCEPT: float = 70.0
    EMB_ACCEPT: float = 0.75  # cosine similarity
    
    # Bonuses/Penalties
    ANCHOR_BONUS: int = 5
    CC_PENALTY: int = -8
    ERR_PENALTY: int = -5
    FIRST_NAME_OVERLAP: int = 5
    LAST_NAME_OVERLAP: int = 5
    INITIALS_MATCH: int = 3
    
    # Limits
    TOP_K_RESULTS: Tuple[int, int] = (3, 5)  # min and max
    MAX_CANDIDATES: int = 5
    MAX_VARIANTS_PER_CANDIDATE: int = 8
    MAX_DESCRIPTION_LENGTH: int = 1000  # chars
    
    # Model
    # Note: L6 variant doesn't exist for multilingual, using L12 (smallest available multilingual model)
    EMBEDDING_MODEL: str = "paraphrase-multilingual-MiniLM-L12-v2"
    
    # Performance
    EMBEDDING_CACHE_SIZE: int = 1000  # future use
    FAISS_ENABLED: bool = False  # future, if users > 50k
    EMBEDDING_TIMEOUT_MS: int = 200  # per-request budget
    
    # Debug
    DEBUG_MODE: bool = False
    
    # Paths
    MODELS_DIR: str = "models"
    USER_ENRICHED_PKL: str = "models/users_enriched.pkl"
    
    def get_top_k(self) -> int:
        """Get the top K value for results (use max for now)."""
        return self.TOP_K_RESULTS[1]


# Global config instance
config = Config()

