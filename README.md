# Deel AI Challenge - Python API

A FastAPI-based REST API for text processing tasks including user-transaction matching and semantic similarity search.

## 📋 Overview

This API implements two main text processing endpoints:

1. **Match Users by Transaction ID**: Finds users likely to match a transaction based on description similarity using fuzzy string matching.
2. **Find Similar Transactions**: Identifies transactions with semantically similar descriptions using sentence embeddings.

## 🚀 Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd deel_ai_challenge
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Prepare your data files:**
   - Place `transactions.csv` in the `data/` directory
   - Place `users.csv` in the `data/` directory
   
   Both CSVs should have the following structure:
   - `transactions.csv`: Must contain columns `id` and `description`
   - `users.csv`: Must contain columns `id` and `name`

## 🏃 Running the API

### Start the server:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`

### Interactive API Documentation:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## 📡 API Endpoints

### 1. Match Users by Transaction ID

**Endpoint:** `GET /match_users/{transaction_id}`

**Description:** Finds users that match a given transaction based on description similarity.

**Parameters:**
- `transaction_id` (path parameter): The ID of the transaction to match

**Response:**
```json
{
  "users": [
    {
      "id": "user_123",
      "match_metric": 95
    }
  ],
  "total_number_of_matches": 10
}
```

**Example:**
```bash
curl http://127.0.0.1:8000/match_users/txn_123
```

### 2. Find Similar Transactions

**Endpoint:** `POST /similar_transactions`

**Description:** Finds transactions with semantically similar descriptions using sentence embeddings.

**Request Body:**
```json
{
  "query": "Salary payment John"
}
```

**Response:**
```json
{
  "transactions": [
    {
      "id": "txn_456",
      "embedding": 0.87
    }
  ],
  "total_number_of_tokens_used": 3
}
```

**Example:**
```bash
curl -X POST "http://127.0.0.1:8000/similar_transactions" \
     -H "Content-Type: application/json" \
     -d '{"query": "Salary payment John"}'
```

### 3. Health Check

**Endpoint:** `GET /health`

**Description:** Returns the health status of the API and data loading status.

## 🧪 Testing

Run the test script (make sure the API server is running):

```bash
python test_api.py
```

Or use the interactive Swagger UI at `http://127.0.0.1:8000/docs` to test endpoints directly.

## 🏗️ Project Structure

```
deel_ai_challenge/
│
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── utils.py                # Data loading utilities
│   ├── routes/
│   │   ├── match_users.py      # User matching logic
│   │   └── similar_transactions.py  # Similarity search logic
│
├── data/
│   ├── transactions.csv        # Transaction data
│   └── users.csv               # User data
│
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── test_api.py                 # API testing script
```

## 🔧 Implementation Details

### Task 1: Match Users by Transaction ID

**Method Used:**
- **Fuzzy String Matching** using `rapidfuzz` library (modern, fast alternative to fuzzywuzzy)
- Uses `token_sort_ratio` for better matching with word order variations
- Case-insensitive comparison
- Returns top 5 matches sorted by similarity score

**How it works:**
1. Retrieves the transaction by ID
2. Extracts the transaction description
3. Compares the description with all user names using fuzzy matching
4. Returns users sorted by match score (0-100 scale)

### Task 2: Find Similar Transactions

**Method Used:**
- **Sentence Embeddings** using `sentence-transformers` library
- Model: `all-MiniLM-L6-v2` (lightweight, fast, and accurate)
- Cosine similarity for semantic comparison
- Embeddings are cached on startup for performance

**How it works:**
1. Encodes all transaction descriptions into embeddings on startup
2. Encodes the input query into an embedding
3. Calculates cosine similarity between query and all transactions
4. Returns top 5 most similar transactions

## ⚠️ Limitations

1. **Performance:**
   - Embeddings are computed on startup and cached in memory, which may be memory-intensive for very large datasets
   - No pagination implemented for large result sets
   - Token counting is simplified (word count) and may not reflect actual tokenizer usage

2. **Accuracy:**
   - Fuzzy matching may not handle all edge cases (e.g., abbreviations, nicknames)
   - Semantic similarity depends on the quality of the pre-trained model
   - No handling of multilingual text

3. **Scalability:**
   - In-memory data storage (CSV files) - not suitable for production at scale
   - No database integration
   - No caching layer for frequently accessed data
   - No batch processing support

4. **Security:**
   - No authentication or authorization
   - No rate limiting
   - No input validation beyond basic type checking

5. **Error Handling:**
   - Limited error handling for edge cases
   - No logging system implemented

## 🚀 Future Improvements (Production-Ready)

### Infrastructure & Scalability

1. **Database Integration:**
   - Replace CSV files with PostgreSQL or MongoDB
   - Implement proper schema with indexes for faster queries
   - Add connection pooling for database connections

2. **Vector Database:**
   - Use specialized vector databases (Pinecone, Weaviate, Qdrant, or FAISS) for faster similarity search
   - Implement approximate nearest neighbor (ANN) search for scalability
   - Add support for hybrid search (keyword + semantic)

3. **Containerization:**
   - Dockerize the application with Dockerfile
   - Create docker-compose.yml for easy deployment
   - Use multi-stage builds for optimized image size

4. **Deployment:**
   - Deploy to cloud platforms (AWS, GCP, Azure)
   - Use Kubernetes for orchestration
   - Implement CI/CD pipelines

### Performance Optimizations

5. **Caching:**
   - Implement Redis for caching frequent queries
   - Cache embeddings for common queries
   - Add TTL-based cache invalidation

6. **Batch Processing:**
   - Support batch queries for multiple transaction IDs
   - Implement async processing for large datasets
   - Add background job processing (Celery, RQ)

### Security & Reliability

7. **Authentication & Authorization:**
   - Implement JWT-based authentication
   - Add role-based access control (RBAC)
   - Secure API keys and credentials

8. **Rate Limiting:**
   - Implement rate limiting per user/IP
   - Add request throttling
   - Monitor API usage

9. **Monitoring & Logging:**
   - Add structured logging (e.g., using Python's logging module)
   - Implement metrics collection (Prometheus, Datadog)
   - Add health checks and alerting

### Enhanced Features

10. **Advanced Embeddings:**
    - Support for OpenAI embeddings (text-embedding-ada-002) for richer semantic understanding
    - Fine-tune models on domain-specific data
    - Support for multilingual embeddings

11. **Better Matching:**
    - Implement fuzzy matching with multiple algorithms (Levenshtein, Jaro-Winkler)
    - Add support for nickname/abbreviation matching
    - Use machine learning models for better user matching

12. **API Enhancements:**
    - Add pagination for large result sets
    - Implement filtering and sorting options
    - Add export functionality (CSV, JSON)

13. **Testing:**
    - Add unit tests (pytest)
    - Add integration tests
    - Implement test coverage reporting

## 📝 Assumptions

1. **Data Format:**
   - CSV files are properly formatted with required columns
   - Transaction IDs and User IDs are unique
   - Descriptions and names are in English (or compatible with the embedding model)

2. **Performance:**
   - Dataset size is manageable for in-memory processing
   - API is used for low to moderate traffic initially

3. **Use Cases:**
   - Primary focus on accuracy over speed for matching tasks
   - Semantic similarity is more important than exact keyword matching for Task 2

## 📚 Dependencies

- **fastapi**: Modern, fast web framework for building APIs
- **uvicorn**: ASGI server for FastAPI
- **pandas**: Data manipulation and analysis
- **rapidfuzz**: Fast fuzzy string matching library (Python 3.12 compatible)
- **sentence-transformers**: Sentence embeddings and semantic similarity

## 👤 Author

Developed as part of the Deel AI Engineer Challenge.

---

**Note:** This is a challenge implementation. For production use, implement the improvements listed above.

