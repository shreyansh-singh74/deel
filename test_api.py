import requests
import json
import copy
from typing import Dict, List, Optional

BASE_URL = "http://127.0.0.1:8000"

def test_match_users(transaction_id: str, expected_user_id: Optional[str] = None, min_score: float = 70.0):
    """
    Test the match_users endpoint with expected results.
    
    Args:
        transaction_id: The ID of the transaction to match
        expected_user_id: Expected user ID that should be in the results (optional)
        min_score: Minimum expected match score (optional)
    """
    url = f"{BASE_URL}/match_users/{transaction_id}"
    print(f"\n🔍 Testing: GET {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Status: {response.status_code}")
        print(f"📊 Response:")
        print(json.dumps(result, indent=2))
        
        # Verify structure
        assert "users" in result, "Response should contain 'users' field"
        assert "total_number_of_matches" in result, "Response should contain 'total_number_of_matches' field"
        
        users = result["users"]
        total_matches = result["total_number_of_matches"]
        
        print(f"\n✓ Found {total_matches} matches above threshold (≥70)")
        
        # Verify all matches are above threshold
        for user in users:
            assert "id" in user, "Each user should have 'id' field"
            assert "match_metric" in user, "Each user should have 'match_metric' field"
            assert user["match_metric"] >= 70, f"Match metric should be ≥70, got {user['match_metric']}"
            assert isinstance(user["match_metric"], (int, float)), "Match metric should be a number"
        
        # Check if expected user is in results
        if expected_user_id:
            user_ids = [u["id"] for u in users]
            if expected_user_id in user_ids:
                expected_user = next(u for u in users if u["id"] == expected_user_id)
                print(f"✓ Expected user '{expected_user_id}' found with score {expected_user['match_metric']}")
            else:
                print(f"⚠ Warning: Expected user '{expected_user_id}' not found in results")
                print(f"  Found users: {user_ids}")
        
        # Check minimum score if provided
        if users and min_score:
            top_score = users[0]["match_metric"]
            if top_score >= min_score:
                print(f"✓ Top match score {top_score} meets minimum expected {min_score}")
            else:
                print(f"⚠ Warning: Top match score {top_score} is below expected {min_score}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return None

def test_similar_transactions(query: str, expected_transaction_ids: Optional[List[str]] = None):
    """
    Test the similar_transactions endpoint with expected results.
    
    Args:
        query: The query string to find similar transactions
        expected_transaction_ids: List of expected transaction IDs that should be in results (optional)
    """
    url = f"{BASE_URL}/similar_transactions"
    print(f"\n🔍 Testing: POST {url}")
    print(f"📝 Query: {query}")
    
    try:
        response = requests.post(url, json={"query": query})
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Status: {response.status_code}")
        print(f"📊 Response:")
        # Print a truncated version for readability (embeddings are long)
        # Use deepcopy to avoid modifying the original result
        result_display = copy.deepcopy(result)
        if "transactions" in result_display:
            for txn in result_display["transactions"]:
                if "embedding" in txn and isinstance(txn["embedding"], list):
                    txn["embedding"] = f"[{len(txn['embedding'])}-dimensional vector]"
        print(json.dumps(result_display, indent=2))
        
        # Verify structure
        assert "transactions" in result, "Response should contain 'transactions' field"
        assert "total_number_of_tokens_used" in result, "Response should contain 'total_number_of_tokens_used' field"
        
        transactions = result["transactions"]
        token_count = result["total_number_of_tokens_used"]
        
        print(f"\n✓ Found {len(transactions)} similar transactions")
        print(f"✓ Token count: {token_count}")
        
        # Verify embedding format
        for txn in transactions:
            assert "id" in txn, "Each transaction should have 'id' field"
            assert "embedding" in txn, "Each transaction should have 'embedding' field"
            assert isinstance(txn["embedding"], list), "Embedding should be a list (vector)"
            assert len(txn["embedding"]) > 0, "Embedding vector should not be empty"
            # all-MiniLM-L6-v2 produces 384-dimensional embeddings
            assert len(txn["embedding"]) == 384, f"Embedding should be 384-dimensional, got {len(txn['embedding'])}"
            # Verify all elements are numbers
            assert all(isinstance(x, (int, float)) for x in txn["embedding"]), "Embedding elements should be numbers"
        
        print(f"✓ All {len(transactions)} transactions have valid 384-dimensional embedding vectors")
        
        # Check if expected transactions are in results
        if expected_transaction_ids:
            found_ids = [txn["id"] for txn in transactions]
            for expected_id in expected_transaction_ids:
                if expected_id in found_ids:
                    print(f"✓ Expected transaction '{expected_id}' found in results")
                else:
                    print(f"⚠ Warning: Expected transaction '{expected_id}' not found in top results")
            print(f"  Found transaction IDs: {found_ids}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return None

def test_health_check():
    """Test the health check endpoint."""
    url = f"{BASE_URL}/health"
    print(f"\n🔍 Testing: GET {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"📊 Response: {json.dumps(result, indent=2)}")
        return result
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    print("=" * 70)
    print("🧪 Testing Deel AI Challenge API with Expected Results")
    print("=" * 70)
    
    # Test health check
    print("\n" + "=" * 70)
    print("Testing Health Check Endpoint")
    print("=" * 70)
    test_health_check()
    
    # ============================================================================
    # TASK 1: Match Users by Transaction ID
    # ============================================================================
    print("\n" + "=" * 70)
    print("TASK 1: Testing Match Users Endpoint")
    print("=" * 70)
    
    print("\n" + "-" * 70)
    print("📋 Test Case 1: RAZbbmLX - 'Transfer from Emma Brown for Deel'")
    print("-" * 70)
    print("Expected: Should match user 'BuCoIvL79A' (Emma Brown) with high score (≥95)")
    result1 = test_match_users("RAZbbmLX", expected_user_id="BuCoIvL79A", min_score=95.0)
    
    print("\n" + "-" * 70)
    print("📋 Test Case 2: D5aW2I5o - 'From James Bennett. for Deel'")
    print("-" * 70)
    print("Expected: Should match user 'XSwFsQlyYa' (James Bennett) with high score (≥95)")
    result2 = test_match_users("D5aW2I5o", expected_user_id="XSwFsQlyYa", min_score=95.0)
    
    print("\n" + "-" * 70)
    print("📋 Test Case 3: aglz0x27 - 'Payment from Sophia Cork for Deel'")
    print("-" * 70)
    print("Expected: Should match user '2xmcoVivzb' (Sophia Cork) with high score (≥95)")
    result3 = test_match_users("aglz0x27", expected_user_id="2xmcoVivzb", min_score=95.0)
    
    print("\n" + "-" * 70)
    print("📋 Test Case 4: caqjJtrI - 'From Liam J. Johnson for Deel'")
    print("-" * 70)
    print("Expected: Should match user 'U4NNQUQIeE' (Liam Johnson) with high score (≥90)")
    result4 = test_match_users("caqjJtrI", expected_user_id="U4NNQUQIeE", min_score=90.0)
    
    print("\n" + "-" * 70)
    print("📋 Test Case 5: Ysop2Dzq - 'Received from !Isabel Wilson for Deel'")
    print("-" * 70)
    print("Expected: Should match user 'ToAD2rzvGA' or 'VfY9DmIkiL' (Isabella Wilson) with high score (≥90)")
    result5 = test_match_users("Ysop2Dzq", expected_user_id=None, min_score=90.0)
    # Check if either Isabella Wilson ID is in results
    if result5:
        user_ids = [u["id"] for u in result5["users"]]
        if "ToAD2rzvGA" in user_ids or "VfY9DmIkiL" in user_ids:
            print("✓ Found Isabella Wilson in results")
    
    print("\n" + "-" * 70)
    print("📋 Test Case 6: rJfl3qKG - 'Request from Charlotte Grace Walker for Deel'")
    print("-" * 70)
    print("Expected: Should match user 'vPYeL2gRtJ' (Charlotte Walker) with high score (≥90)")
    result6 = test_match_users("rJfl3qKG", expected_user_id="vPYeL2gRtJ", min_score=90.0)
    
    # ============================================================================
    # TASK 2: Find Similar Transactions
    # ============================================================================
    print("\n" + "=" * 70)
    print("TASK 2: Testing Similar Transactions Endpoint")
    print("=" * 70)
    
    print("\n" + "-" * 70)
    print("📋 Test Case 1: 'Payment from Benjamin for Deel'")
    print("-" * 70)
    print("Expected: Should find transactions with Benjamin in description:")
    print("  - zKzUOlWx: 'From Benjamin Leedsfor Deel'")
    print("  - 62O2d9rm: 'Payment from Benjamin Rivera for Deel'")
    print("  - kXAGOWZ4: 'From Benjamin Lee Test for Deel'")
    result7 = test_similar_transactions(
        "Payment from Benjamin for Deel",
        expected_transaction_ids=["zKzUOlWx", "62O2d9rm", "kXAGOWZ4"]
    )
    
    print("\n" + "-" * 70)
    print("📋 Test Case 2: 'Payment from Lily for Deel'")
    print("-" * 70)
    print("Expected: Should find transactions with Lily in description:")
    print("  - iMsNYIes: 'From Lily Kelly01 for Deel'")
    print("  - OuFHALqM: 'from Lily, Foster for Deel'")
    result8 = test_similar_transactions(
        "Payment from Lily for Deel",
        expected_transaction_ids=["iMsNYIes", "OuFHALqM"]
    )
    
    print("\n" + "-" * 70)
    print("📋 Test Case 3: 'Transfer from Emma Brown for Deel'")
    print("-" * 70)
    print("Expected: Should find transaction 'RAZbbmLX' (Transfer from Emma Brown)")
    result9 = test_similar_transactions(
        "Transfer from Emma Brown for Deel",
        expected_transaction_ids=["RAZbbmLX"]
    )
    
    print("\n" + "-" * 70)
    print("📋 Test Case 4: 'From James Bennett for Deel'")
    print("-" * 70)
    print("Expected: Should find transaction 'D5aW2I5o' (From James Bennett. for Deel)")
    result10 = test_similar_transactions(
        "From James Bennett for Deel",
        expected_transaction_ids=["D5aW2I5o"]
    )
    
    print("\n" + "-" * 70)
    print("📋 Test Case 5: 'Payment from employee'")
    print("-" * 70)
    print("Expected: Should find various payment transactions")
    result11 = test_similar_transactions("Payment from employee")
    
    print("\n" + "=" * 70)
    print("✅ All tests completed!")
    print("=" * 70)
    print("\n📝 Summary:")
    print("  - Task 1 (Match Users): Tests verify that transaction descriptions")
    print("    correctly extract names and match them to users in the database.")
    print("  - Task 2 (Similar Transactions): Tests verify that semantic similarity")
    print("    search finds transactions with similar meanings to the query.")
    print("\n💡 Note: The 'embedding' field in Task 2 contains the actual")
    print("    384-dimensional embedding vector, not a similarity score.")
