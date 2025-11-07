from sentence_transformers import SentenceTransformer, util
import torch
import pandas as pd

# Load the model once when module is imported
model = SentenceTransformer('all-MiniLM-L6-v2')

# Cache embeddings for transactions to avoid recomputing
_transaction_embeddings = None
_transaction_descriptions = None

def initialize_transaction_embeddings(transactions: pd.DataFrame):
    """
    Initialize and cache transaction embeddings for faster lookups.
    
    Args:
        transactions: DataFrame containing transaction data
    """
    global _transaction_embeddings, _transaction_descriptions
    
    descriptions = transactions["description"].tolist()
    _transaction_descriptions = descriptions
    _transaction_embeddings = model.encode(descriptions, convert_to_tensor=True, show_progress_bar=True)

def similar_transactions(input_text: str, transactions: pd.DataFrame):
    """
    Find transactions with semantically similar descriptions.
    
    Args:
        input_text: The query string to find similar transactions
        transactions: DataFrame containing transaction data
        
    Returns:
        dict: Dictionary with similar transactions (with similarity scores, without embeddings) and token count
    """
    global _transaction_embeddings, _transaction_descriptions
    
    # Initialize embeddings if not already done
    if _transaction_embeddings is None:
        initialize_transaction_embeddings(transactions)
    
    # Encode the input text
    input_embedding = model.encode(input_text, convert_to_tensor=True)
    
    # Calculate cosine similarity
    cosine_scores = util.pytorch_cos_sim(input_embedding, _transaction_embeddings)[0]
    
    # Get top 5 most similar transactions
    sorted_indices = torch.argsort(cosine_scores, descending=True)
    
    results = []
    for idx in sorted_indices[:5]:
        transaction_idx = idx.item()
        similarity_score = cosine_scores[idx].item()
        
        results.append({
            "id": transactions.iloc[transaction_idx]["id"],
            "description": transactions.iloc[transaction_idx]["description"],
            "similarity_score": round(similarity_score, 4)
        })
    
    # Count tokens using the model's tokenizer (accurate token counting)
    # Access tokenizer from the underlying transformer model
    try:
        # Try direct access (most common case)
        tokenizer = model.tokenizer
        tokens = tokenizer.tokenize(input_text)
        total_tokens = len(tokens)
    except AttributeError:
        # Fallback: try accessing through the first module
        try:
            tokenizer = model[0].tokenizer
            tokens = tokenizer.tokenize(input_text)
            total_tokens = len(tokens)
        except (AttributeError, IndexError):
            # Final fallback: use encode and count tokens from the output
            # Access through the first module's tokenizer
            encoded = model[0].tokenizer.encode(input_text, add_special_tokens=True)
            total_tokens = len(encoded)
    
    return {
        "transactions": results,
        "total_number_of_tokens_used": total_tokens
    }


