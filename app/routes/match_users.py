from rapidfuzz import fuzz
import pandas as pd

def match_users(transaction_id: str, transactions: pd.DataFrame, users: pd.DataFrame):
    """
    Match users to a transaction based on description similarity.
    
    Args:
        transaction_id: The ID of the transaction to match
        transactions: DataFrame containing transaction data
        users: DataFrame containing user data
        
    Returns:
        dict: Dictionary with matched users and total count
    """
    # Find the transaction
    transaction = transactions[transactions["id"] == transaction_id]
    
    if transaction.empty:
        return {"error": "Transaction not found"}
    
    # Get the description from the transaction
    description = transaction.iloc[0]["description"]
    
    # Calculate similarity scores for all users
    results = []
    for _, user in users.iterrows():
        # Use token_sort_ratio for better matching with word order variations
        score = fuzz.token_sort_ratio(
            str(description).lower(), 
            str(user["name"]).lower()
        )
        results.append({
            "id": user["id"],
            "match_metric": score
        })
    
    # Sort by match score (descending)
    results = sorted(results, key=lambda x: x["match_metric"], reverse=True)
    
    return {
        "users": results[:5],  # Return top 5 matches
        "total_number_of_matches": len(results)
    }

