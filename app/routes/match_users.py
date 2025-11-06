from rapidfuzz import fuzz
import pandas as pd
import re

def extract_name_from_description(description: str) -> str:
    """
    Extract potential name(s) from transaction description.
    
    Handles patterns like:
    - "From <name> for Deel"
    - "Transfer from <name> for Deel"
    - "Received from <name> for Deel"
    - "Payment from <name> for Deel"
    - "Request from <name> for Deel"
    
    Args:
        description: Transaction description string
        
    Returns:
        Extracted name string, or empty string if no name found
    """
    if not description:
        return ""
    
    # Pattern 1: "From <name> for Deel" or "From <name>, for Deel"
    pattern1 = r'From\s+([A-Z][a-zA-Z\s\.\']+(?:\s+[A-Z][a-zA-Z\s\.\']*)*?)(?:\s*,?\s*for\s+Deel|$)'
    match1 = re.search(pattern1, description, re.IGNORECASE)
    if match1:
        name = match1.group(1).strip()
        # Clean up the name (remove extra spaces, trailing punctuation)
        name = re.sub(r'\s+', ' ', name).strip()
        name = re.sub(r'[^\w\s\.\'-]', '', name).strip()
        if name and len(name) > 1:
            return name
    
    # Pattern 2: "Transfer from <name> for Deel"
    pattern2 = r'Transfer\s+from\s+([A-Z][a-zA-Z\s\.\']+(?:\s+[A-Z][a-zA-Z\s\.\']*)*?)(?:\s*,?\s*for\s+Deel|$)'
    match2 = re.search(pattern2, description, re.IGNORECASE)
    if match2:
        name = match2.group(1).strip()
        name = re.sub(r'\s+', ' ', name).strip()
        name = re.sub(r'[^\w\s\.\'-]', '', name).strip()
        if name and len(name) > 1:
            return name
    
    # Pattern 3: "Received from <name> for Deel"
    pattern3 = r'Received\s+from\s+([A-Z][a-zA-Z\s\.\']+(?:\s+[A-Z][a-zA-Z\s\.\']*)*?)(?:\s*,?\s*for\s+Deel|$)'
    match3 = re.search(pattern3, description, re.IGNORECASE)
    if match3:
        name = match3.group(1).strip()
        name = re.sub(r'\s+', ' ', name).strip()
        name = re.sub(r'[^\w\s\.\'-]', '', name).strip()
        if name and len(name) > 1:
            return name
    
    # Pattern 4: "Payment from <name> for Deel"
    pattern4 = r'Payment\s+from\s+([A-Z][a-zA-Z\s\.\']+(?:\s+[A-Z][a-zA-Z\s\.\']*)*?)(?:\s*,?\s*for\s+Deel|$)'
    match4 = re.search(pattern4, description, re.IGNORECASE)
    if match4:
        name = match4.group(1).strip()
        name = re.sub(r'\s+', ' ', name).strip()
        name = re.sub(r'[^\w\s\.\'-]', '', name).strip()
        if name and len(name) > 1:
            return name
    
    # Pattern 5: "Request from <name> for Deel"
    pattern5 = r'Request\s+from\s+([A-Z][a-zA-Z\s\.\']+(?:\s+[A-Z][a-zA-Z\s\.\']*)*?)(?:\s*,?\s*for\s+Deel|$)'
    match5 = re.search(pattern5, description, re.IGNORECASE)
    if match5:
        name = match5.group(1).strip()
        name = re.sub(r'\s+', ' ', name).strip()
        name = re.sub(r'[^\w\s\.\'-]', '', name).strip()
        if name and len(name) > 1:
            return name
    
    # Pattern 6: "Deel payment from <name> for Deel"
    pattern6 = r'Deel\s+payment\s+from\s+([A-Z][a-zA-Z\s\.\']+(?:\s+[A-Z][a-zA-Z\s\.\']*)*?)(?:\s*,?\s*for\s+Deel|$)'
    match6 = re.search(pattern6, description, re.IGNORECASE)
    if match6:
        name = match6.group(1).strip()
        name = re.sub(r'\s+', ' ', name).strip()
        name = re.sub(r'[^\w\s\.\'-]', '', name).strip()
        if name and len(name) > 1:
            return name
    
    return ""

def match_users(transaction_id: str, transactions: pd.DataFrame, users: pd.DataFrame):
    """
    Match users to a transaction based on description similarity.
    
    Extracts potential names from transaction descriptions and matches them
    against user names using fuzzy string matching.
    
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
    
    # Extract potential name from description
    extracted_name = extract_name_from_description(str(description))
    
    # If no name extracted, fall back to using description (but this is less ideal)
    if not extracted_name:
        extracted_name = str(description)
    
    # Calculate similarity scores for all users
    results = []
    for _, user in users.iterrows():
        user_name = str(user["name"]).strip()
        if not user_name:
            continue
            
        # Use token_sort_ratio for better matching with word order variations
        score = fuzz.token_sort_ratio(
            extracted_name.lower(), 
            user_name.lower()
        )
        
        # Only include matches above threshold (≥70)
        if score >= 70:
            results.append({
                "id": user["id"],
                "match_metric": round(score, 2)
            })
    
    # Sort by match score (descending)
    results = sorted(results, key=lambda x: x["match_metric"], reverse=True)
    
    return {
        "users": results,
        "total_number_of_matches": len(results)
    }

