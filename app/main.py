from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from app.utils import load_data
from app.routes.match_users import match_users
from app.routes.similar_transactions import similar_transactions, initialize_transaction_embeddings
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI(
    title="Deel AI Challenge API",
    description="API for matching users to transactions and finding similar transactions",
    version="1.0.0"
)

# Load data on startup
transactions, users = load_data()

# Initialize transaction embeddings on startup
@app.on_event("startup")
async def startup_event():
    """Initialize transaction embeddings when the API starts."""
    print("Initializing transaction embeddings...")
    initialize_transaction_embeddings(transactions)
    print("Transaction embeddings initialized!")

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
    result = match_users(transaction_id, transactions, users)
    
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
    return {"status": "healthy", "data_loaded": len(transactions) > 0 and len(users) > 0}
 

