import pandas as pd
import os

def load_data():
    """
    Load transactions and users data from CSV files.
    
    Returns:
        tuple: (transactions DataFrame, users DataFrame)
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    transactions_path = os.path.join(base_dir, "data", "transactions.csv")
    users_path = os.path.join(base_dir, "data", "users.csv")
    
    transactions = pd.read_csv(transactions_path)
    users = pd.read_csv(users_path)
    
    return transactions, users