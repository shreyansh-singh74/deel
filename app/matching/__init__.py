"""Matching module for candidate extraction and matching."""
from app.matching.candidate_extractor import CandidateExtractor
from app.matching.candidate_normalizer import CandidateNormalizer
from app.matching.fuzzy_matcher import FuzzyMatcher
from app.matching.embedding_matcher import EmbeddingMatcher
from app.matching.disambiguator import Disambiguator

__all__ = [
    'CandidateExtractor',
    'CandidateNormalizer',
    'FuzzyMatcher',
    'EmbeddingMatcher',
    'Disambiguator'
]

