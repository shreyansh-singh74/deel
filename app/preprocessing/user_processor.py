"""User preprocessing for normalization and embedding generation."""
import os
import pickle
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from unidecode import unidecode
from sentence_transformers import SentenceTransformer

from app.config.settings import config


class UserPreprocessor:
    """Preprocess users: normalize names and precompute embeddings."""
    
    def __init__(self, embedding_model: Optional[SentenceTransformer] = None):
        """
        Initialize UserPreprocessor.
        
        Args:
            embedding_model: Optional pre-loaded embedding model
        """
        self.embedding_model = embedding_model
        self.model_dim = None
        # If model is provided, get its dimension
        if self.embedding_model is not None:
            test_embedding = self.embedding_model.encode(["test"])
            self.model_dim = test_embedding.shape[1]
    
    @staticmethod
    def strip_accents(text: str) -> str:
        """
        Strip diacritics using unidecode.
        
        Args:
            text: Text with possible diacritics
            
        Returns:
            Text with diacritics stripped
        """
        if not text:
            return ""
        return unidecode(text)
    
    @staticmethod
    def generate_initials(tokens: List[str]) -> str:
        """
        Generate initials from tokens.
        
        Args:
            tokens: List of token strings
            
        Returns:
            Initials string (first char of each token)
        """
        if not tokens:
            return ""
        return "".join(token[0].upper() if token else "" for token in tokens)
    
    @staticmethod
    def generate_reversed_name(tokens: List[str]) -> Optional[str]:
        """
        Generate reversed name if exactly 2 tokens.
        
        Args:
            tokens: List of token strings
            
        Returns:
            Reversed name string or None
        """
        if len(tokens) == 2:
            return f"{tokens[1]} {tokens[0]}"
        return None
    
    def preprocess_users(
        self, 
        users_df: pd.DataFrame,
        cache_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Preprocess users: normalize and compute embeddings.
        
        Args:
            users_df: DataFrame with 'id' and 'name' columns
            cache_path: Optional path to cache file
            
        Returns:
            List of preprocessed user records
        """
        # Try to load from cache
        if cache_path and os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    cached_data = pickle.load(f)
                    # Verify cache is valid
                    if 'users' in cached_data and 'model_dim' in cached_data:
                        print(f"Loaded {len(cached_data['users'])} preprocessed users from cache")
                        self.model_dim = cached_data['model_dim']
                        return cached_data['users']
            except Exception as e:
                print(f"Failed to load cache: {e}, recomputing...")
        
        # Load or create embedding model
        if self.embedding_model is None:
            print(f"Loading embedding model: {config.EMBEDDING_MODEL}")
            self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
        
        # Ensure model_dim is set
        if self.model_dim is None:
            # Get model dimension
            test_embedding = self.embedding_model.encode(["test"])
            self.model_dim = test_embedding.shape[1]
        
        preprocessed_users = []
        names_to_embed = []
        user_indices = []
        
        # Process each user
        for idx, row in users_df.iterrows():
            user_id = str(row.get('id', ''))
            name_raw = str(row.get('name', '')).strip()
            
            # Skip empty names
            if not user_id or not name_raw or name_raw.lower() in ['nan', 'none', '']:
                continue
            
            # Normalize
            name_lc = name_raw.lower().strip()
            name_strip_accents = self.strip_accents(name_lc)
            
            if not name_strip_accents:
                continue
            
            # Tokenize
            tokens = [t.strip() for t in name_strip_accents.split() if t.strip()]
            if not tokens:
                continue
            
            # Generate features
            initials = self.generate_initials(tokens)
            reversed_name = self.generate_reversed_name(tokens)
            
            # Store user data
            user_record = {
                'id': user_id,
                'name_raw': name_raw,
                'name_lc': name_lc,
                'name_strip_accents': name_strip_accents,
                'tokens': tokens,
                'initials': initials,
                'reversed_name': reversed_name,
                'embedding': None  # Will be filled after batch encoding
            }
            
            preprocessed_users.append(user_record)
            names_to_embed.append(name_strip_accents)
            user_indices.append(len(preprocessed_users) - 1)
        
        # Batch encode embeddings
        if names_to_embed:
            print(f"Computing embeddings for {len(names_to_embed)} users...")
            embeddings = self.embedding_model.encode(
                names_to_embed,
                convert_to_numpy=True,
                show_progress_bar=True
            )
            
            # Assign embeddings
            for i, user_idx in enumerate(user_indices):
                preprocessed_users[user_idx]['embedding'] = embeddings[i]
            
            # Validate embeddings
            for user in preprocessed_users:
                if user['embedding'] is not None:
                    assert user['embedding'].shape[0] == self.model_dim, \
                        f"Embedding dimension mismatch: {user['embedding'].shape[0]} != {self.model_dim}"
        
        # Save to cache
        if cache_path:
            try:
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                with open(cache_path, 'wb') as f:
                    pickle.dump({
                        'users': preprocessed_users,
                        'model_dim': self.model_dim
                    }, f)
                print(f"Saved preprocessed users to {cache_path}")
            except Exception as e:
                print(f"Failed to save cache: {e}")
        
        print(f"Preprocessed {len(preprocessed_users)} users")
        return preprocessed_users
    
    def get_user_dict(self, preprocessed_users: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Convert preprocessed users list to dictionary keyed by user ID.
        
        Args:
            preprocessed_users: List of preprocessed user records
            
        Returns:
            Dictionary keyed by user ID
        """
        return {user['id']: user for user in preprocessed_users}
    
    def get_all_user_tokens(self, preprocessed_users: List[Dict[str, Any]]) -> List[str]:
        """
        Get all unique tokens from all users for glued word detection.
        
        Args:
            preprocessed_users: List of preprocessed user records
            
        Returns:
            List of unique tokens
        """
        all_tokens = set()
        for user in preprocessed_users:
            all_tokens.update(user['tokens'])
        return list(all_tokens)

