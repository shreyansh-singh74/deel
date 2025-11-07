from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from sentence_transformers import SentenceTransformer
from app.utils import load_data
from app.routes.match_users import match_users
from app.routes.similar_transactions import similar_transactions, initialize_transaction_embeddings
from app.config.settings import config
from app.preprocessing.user_processor import UserPreprocessor
from app.observability.logger import RequestLogger
from pydantic import BaseModel
import os

# Initialize FastAPI app
app = FastAPI(
    title="Deel AI Challenge API",
    description="API for matching users to transactions and finding similar transactions",
    version="1.0.0"
)

# Global variables for preprocessed data
preprocessed_users = []
user_embedding_model = None
request_logger = None

# Load data on startup
transactions, users = load_data()

# Initialize user preprocessing and embeddings on startup
@app.on_event("startup")
async def startup_event():
    """Initialize user preprocessing, embeddings, and transaction embeddings when the API starts."""
    global preprocessed_users, user_embedding_model, request_logger
    
    print("Initializing user preprocessing and embeddings...")
    
    # Load multilingual embedding model for user matching
    print(f"Loading embedding model: {config.EMBEDDING_MODEL}")
    user_embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
    
    # Initialize user preprocessor
    user_processor = UserPreprocessor(embedding_model=user_embedding_model)
    
    # Preprocess users (load from cache if available)
    cache_path = config.USER_ENRICHED_PKL
    preprocessed_users = user_processor.preprocess_users(users, cache_path=cache_path)
    
    print(f"Preprocessed {len(preprocessed_users)} users")
    print("User preprocessing completed!")
    
    # Initialize transaction embeddings
    print("Initializing transaction embeddings...")
    initialize_transaction_embeddings(transactions)
    print("Transaction embeddings initialized!")
    
    # Initialize request logger
    request_logger = RequestLogger(debug_mode=config.DEBUG_MODE)
    print("Request logger initialized!")
    
    print("Startup complete!")

# Request model for similar_transactions endpoint
class SimilarTransactionsRequest(BaseModel):
    query: str

@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "message": "Deel AI Challenge API",
        "endpoints": {
            "match_users": "/match_users/{transaction_id}",
            "similar_transactions": "/similar_transactions"
        }
    }

@app.get("/match_users/{transaction_id}")
def get_matched_users(transaction_id: str):
    """
    Match users to a transaction based on description similarity.
    
    Args:
        transaction_id: The ID of the transaction to match
        
    Returns:
        JSON response with matched users
    """
    if not preprocessed_users or user_embedding_model is None:
        raise HTTPException(
            status_code=503,
            detail="Service not ready: user preprocessing not completed"
        )
    
    result = match_users(
        transaction_id,
        transactions,
        preprocessed_users,
        user_embedding_model,
        logger=request_logger
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return JSONResponse(content=result)

@app.post("/similar_transactions")
def get_similar_transactions(request: SimilarTransactionsRequest):
    """
    Find transactions with semantically similar descriptions.
    
    Args:
        request: Request body containing the query string
        
    Returns:
        JSON response with similar transactions
    """
    result = similar_transactions(request.query, transactions)
    return JSONResponse(content=result)

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "data_loaded": len(transactions) > 0 and len(users) > 0,
        "users_preprocessed": len(preprocessed_users) > 0,
        "embedding_model_loaded": user_embedding_model is not None
    }
