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
      "name": "John Doe",
      "match_metric": 95,
      "method": "fuzzy"
    }
  ],
  "total_number_of_matches": 10
}
```

**Response Fields:**
- `id`: User ID
- `name`: User's full name
- `match_metric`: Match score (0-100), where 100 is a perfect match
- `method`: Matching method used (`"fuzzy"` or `"embedding"`)

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
      "embedding": [0.123, 0.456, 0.789, ...]
    }
  ],
  "total_number_of_tokens_used": 3
}
```

**Note:** The `embedding` field contains the actual embedding vector (384-dimensional for all-MiniLM-L6-v2), not a similarity score.

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
│   ├── config/
│   │   └── settings.py         # Centralized configuration
│   ├── preprocessing/
│   │   ├── user_processor.py   # User normalization and embedding
│   │   └── text_cleaner.py     # Text cleaning utilities
│   ├── matching/
│   │   ├── candidate_extractor.py      # Name extraction
│   │   ├── candidate_normalizer.py     # Variant generation
│   │   ├── fuzzy_matcher.py            # Fuzzy matching
│   │   ├── embedding_matcher.py        # Embedding matching
│   │   ├── disambiguator.py            # Disambiguation logic
│   │   ├── transliteration_map.py      # Non-Latin transliteration
│   │   └── misspelling_map.py          # Common misspellings
│   ├── observability/
│   │   └── logger.py           # Request logging and metrics
│   └── routes/
│       ├── match_users.py      # User matching endpoint
│       └── similar_transactions.py  # Similarity search logic
│
├── data/
│   ├── transactions.csv        # Transaction data
│   └── users.csv               # User data
│
├── models/
│   └── users_enriched.pkl      # Cached preprocessed users
│
├── tests/
│   └── test_match_users.py     # Unit tests
│
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── test_api.py                 # API testing script
```

## 🔧 Implementation Details

### Task 1: Match Users by Transaction ID

**Hybrid Pipeline:**
- **Fuzzy Matching (First Pass)**: Fast fuzzy string matching using `rapidfuzz` library
- **Embedding Fallback**: Multilingual sentence embeddings for hard cases (non-Latin scripts, complex typos)
- **Anchor-driven Extraction**: Intelligent name extraction from transaction descriptions
- **Robust Normalization**: Handles typos, diacritics, glued words, reversed names, and more

**Pipeline Steps:**
1. **Text Normalization**: Soft clean (for extraction) and hard clean (for fallback) of transaction descriptions
2. **Candidate Extraction**: Anchor-driven extraction using patterns:
   - After "from" anchor
   - After "ref:" anchor
   - Before "for deel" anchor
   - Fallback: sliding windows for noisy text
3. **Candidate Normalization**: Generate variants (reversed order, remove initials, drop digits, transliteration)
4. **Fuzzy Matching**: Fast fuzzy matching with bonuses/penalties:
   - Base score from multiple fuzzy metrics (token_sort_ratio, partial_ratio, jaro_winkler)
   - Bonuses: +5 first-name overlap, +5 last-name overlap, +3 initials match
   - Penalties: -8 if in CC region, -5 if near error markers
   - Accept if top score ≥ 70
5. **Embedding Fallback**: If fuzzy fails (<70), use multilingual embeddings:
   - Transliteration for known non-Latin names (Chinese, Greek, Hebrew)
   - Cosine similarity with precomputed user embeddings
   - Accept if top cosine ≥ 0.75 (scaled to 0-100)
6. **Disambiguation**: Apply anchor bonuses, CC penalties, prefer compound names
7. **Output**: Return top 3-5 matches with method and score

**Thresholds:**
- Fuzzy accept: **≥ 70**
- Embedding accept: **cosine ≥ 0.75** (scaled to 0-100)
- Return top: **3-5 results**

**Edge Cases Handled:**
1. Noise/boilerplate removal
2. Nonstandard name positions
3. Typos and glued words
4. Case variations
5. Diacritics (é → e)
6. Non-Latin scripts (Chinese, Greek, Hebrew) with transliteration
7. Digits in names (0→o, 1→l, kelly01→kelly)
8. Initials and suffixes (J., K, jr)
9. Multi-person mentions (CC handling)
10. Reversed name order (Fisher Victoria → Victoria Fisher)
11. Compound/merged names (matthewbrooks → matthew brooks)
12. Ambiguous "From for Deel" patterns
13. Multiple candidates with same first names
14. Translation vs transliteration
15. Whitespace chaos
16. Punctuation garbage
17. Near-miss users
18. Multiple name-like tokens
19. Duplicate users (same name, different IDs)
20. Blank/malformed user names

### Task 2: Find Similar Transactions

**Method Used:**
- **Sentence Embeddings** using `sentence-transformers` library
- Model: `all-MiniLM-L6-v2` (lightweight, fast, and accurate)
- Cosine similarity for semantic comparison
- Embeddings are cached on startup for performance
- **Accurate token counting** using the model's tokenizer

**How it works:**
1. Encodes all transaction descriptions into embeddings on startup (cached in memory)
2. Encodes the input query into an embedding
3. Calculates cosine similarity between query and all transactions
4. Ranks transactions by similarity score
5. Returns top 5 most similar transactions with their **actual embedding vectors** (384-dimensional)
6. Counts tokens using the model's tokenizer for accurate token usage reporting

## ⚠️ Limitations

1. **Performance:**
   - Embeddings are computed on startup and cached in memory, which may be memory-intensive for very large datasets
   - No pagination implemented for large result sets
   - In-memory similarity search may be slow for datasets with 100k+ transactions

2. **Accuracy:**
   - Handles 20+ edge cases including typos, non-Latin scripts, and noisy text
   - Hybrid approach (fuzzy + embedding) provides good coverage
   - Very uncommon transliterations outside the provided map might fall back to embeddings that are slightly less certain
   - If names are fully absent from descriptions, the model returns empty
   - Thresholds are tunable via configuration (config/settings.py)

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

## 🚀 Task 3: Production Scaling Plan

This section outlines a comprehensive strategy for scaling this API to production-ready standards, handling millions of transactions and high request volumes.

### Database Migration Strategy

**PostgreSQL Integration:**
- **Replace CSV files** with PostgreSQL database for persistent, scalable data storage
- **Schema Design:**
  ```sql
  CREATE TABLE users (
      id VARCHAR PRIMARY KEY,
      name VARCHAR NOT NULL,
      created_at TIMESTAMP DEFAULT NOW(),
      updated_at TIMESTAMP DEFAULT NOW()
  );
  
  CREATE TABLE transactions (
      id VARCHAR PRIMARY KEY,
      amount DECIMAL(10, 2),
      description TEXT NOT NULL,
      user_id VARCHAR REFERENCES users(id),
      created_at TIMESTAMP DEFAULT NOW(),
      updated_at TIMESTAMP DEFAULT NOW()
  );
  
  CREATE INDEX idx_transactions_description ON transactions USING gin(to_tsvector('english', description));
  CREATE INDEX idx_users_name ON users(name);
  ```
- **Connection Pooling:** Use SQLAlchemy with connection pooling (e.g., 20-50 connections)
- **Read Replicas:** Implement read replicas for scaling read operations
- **Migration Path:** Use Alembic for database migrations and version control

### Vector Database for Embeddings

**Why Vector Databases:**
- Current in-memory approach doesn't scale beyond ~100k transactions
- Vector databases provide fast approximate nearest neighbor (ANN) search
- Support for incremental updates without full recomputation

**Recommended Options:**

1. **FAISS (Facebook AI Similarity Search)**
   - Open-source, self-hosted
   - Best for: Large-scale deployments with full control
   - Implementation: Store embeddings in FAISS index, update incrementally
   - Pros: Fast, free, no external dependencies
   - Cons: Requires manual management, no built-in persistence

2. **Chroma**
   - Open-source, lightweight
   - Best for: Medium-scale deployments, easy integration
   - Implementation: Store embeddings with metadata, query by similarity
   - Pros: Simple API, good documentation, local or cloud options
   - Cons: Less mature than commercial solutions

3. **Pinecone**
   - Managed service
   - Best for: Production deployments requiring minimal ops overhead
   - Implementation: Upload embeddings via API, query by similarity
   - Pros: Fully managed, auto-scaling, high performance
   - Cons: Cost per query, vendor lock-in

4. **Qdrant**
   - Open-source with managed option
   - Best for: Balance of control and ease of use
   - Implementation: REST API for embedding storage and search
   - Pros: Good performance, flexible deployment options
   - Cons: Requires infrastructure management (self-hosted)

**Implementation Strategy:**
- Precompute embeddings for all existing transactions and store in vector DB
- For new transactions: compute embeddings asynchronously and update vector DB
- Use hybrid search (keyword + semantic) for better accuracy
- Implement embedding versioning to support model updates

### Async Background Tasks

**Embedding Updates:**
- Use **Celery** or **RQ (Redis Queue)** for background job processing
- When new transaction is created:
  1. Store transaction in PostgreSQL immediately
  2. Queue background task to compute embedding
  3. Update vector database asynchronously
  4. Cache result for faster subsequent queries

**Example Architecture:**
```python
from celery import Celery

celery_app = Celery('tasks', broker='redis://localhost:6379')

@celery_app.task
def compute_and_store_embedding(transaction_id: str):
    # Fetch transaction from DB
    # Compute embedding
    # Store in vector database
    # Update cache
    pass
```

**Benefits:**
- Non-blocking API responses
- Better resource utilization
- Ability to retry failed embedding computations
- Batch processing for bulk imports

### Containerization and Deployment

**Docker Setup:**
- Multi-stage Dockerfile for optimized image size
- Separate containers for:
  - API server (FastAPI + Uvicorn)
  - Background workers (Celery)
  - Database (PostgreSQL)
  - Vector database (if self-hosted)
  - Redis (for caching and task queue)

**Docker Compose Example:**
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
  
  worker:
    build: .
    command: celery -A app.tasks worker
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
```

**Deployment Options:**

1. **AWS:**
   - **ECS (Elastic Container Service)** for container orchestration
   - **RDS PostgreSQL** for managed database
   - **ElastiCache Redis** for caching
   - **Lambda** for serverless embedding updates (if applicable)
   - **CloudWatch** for monitoring and logging

2. **GCP:**
   - **Cloud Run** for serverless container deployment
   - **Cloud SQL** for managed PostgreSQL
   - **Memorystore** for Redis
   - **Cloud Functions** for background tasks
   - **Cloud Monitoring** for observability

3. **Azure:**
   - **Container Instances** or **AKS** for containers
   - **Azure Database for PostgreSQL**
   - **Azure Cache for Redis**
   - **Azure Functions** for serverless tasks
   - **Application Insights** for monitoring

**Kubernetes (for large-scale):**
- Deploy API, workers, and services as Kubernetes pods
- Use Horizontal Pod Autoscaling based on CPU/memory
- Implement service mesh (Istio) for advanced traffic management
- Use Helm charts for easy deployment and updates

### API Key Authentication and Rate Limiting

**Authentication:**
- Implement **JWT (JSON Web Tokens)** or **API Key** authentication
- Use FastAPI's `HTTPBearer` or custom API key middleware
- Store API keys in secure environment variables or secrets manager (AWS Secrets Manager, HashiCorp Vault)
- Implement role-based access control (RBAC) for different user tiers

**Rate Limiting:**
- Use **slowapi** (FastAPI rate limiting) or **Redis** for distributed rate limiting
- Implement tiered limits:
  - Free tier: 100 requests/hour
  - Pro tier: 1000 requests/hour
  - Enterprise: Custom limits
- Return appropriate HTTP 429 (Too Many Requests) with retry-after headers

**Example Implementation:**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/match_users/{transaction_id}")
@limiter.limit("10/minute")
async def match_users(request: Request, transaction_id: str):
    # ... implementation
```

### Model Fine-Tuning and Optimization

**Domain-Specific Fine-Tuning:**
- Fine-tune the embedding model on Deel-specific transaction text
- Collect labeled pairs of similar transactions
- Use contrastive learning to improve semantic understanding
- Retrain periodically as transaction patterns evolve

**Benefits:**
- Better understanding of financial/transaction terminology
- Improved matching for domain-specific phrases
- Higher accuracy for similar transaction detection

**Implementation Approach:**
1. Collect training data: pairs of similar transactions (manually labeled or from user feedback)
2. Fine-tune `all-MiniLM-L6-v2` using sentence-transformers training framework
3. Evaluate on held-out test set
4. Deploy new model version with A/B testing
5. Monitor performance metrics and rollback if needed

**Alternative: Use Domain-Specific Models:**
- Consider using OpenAI's `text-embedding-ada-002` for richer embeddings (if budget allows)
- Evaluate multilingual models if supporting international transactions
- Use ensemble methods combining multiple embedding models

### Monitoring and Observability

**Logging:**
- Structured logging with JSON format (using Python's `logging` module)
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Include request IDs, user IDs, transaction IDs for traceability
- Centralized logging: ELK stack, Datadog, or CloudWatch Logs

**Metrics:**
- **Application Metrics:**
  - Request latency (p50, p95, p99)
  - Request rate (requests/second)
  - Error rate (4xx, 5xx responses)
  - Embedding computation time
  - Database query latency
  
- **Business Metrics:**
  - Match accuracy (if feedback available)
  - Average similarity scores
  - Token usage per request
  - Cache hit rates

**Tools:**
- **Prometheus** + **Grafana** for metrics visualization
- **Datadog** or **New Relic** for APM (Application Performance Monitoring)
- **Sentry** for error tracking and alerting

### Additional Production Considerations

**Caching Strategy:**
- **Redis** for caching:
  - Frequently accessed transaction embeddings
  - User matching results (with TTL)
  - Similar transaction queries (cache key = query hash)
- Cache invalidation: TTL-based or event-driven (when new transactions added)

**Load Balancing:**
- Use **NGINX** or cloud load balancer (AWS ALB, GCP Load Balancer)
- Health checks for API instances
- Session affinity if needed (though stateless is preferred)

**Disaster Recovery:**
- Database backups: Daily automated backups with point-in-time recovery
- Vector database backups: Regular snapshots of embedding indices
- Multi-region deployment for high availability
- Failover procedures documented and tested

**Cost Optimization:**
- Right-size compute resources based on actual usage
- Use spot instances for background workers (if on AWS)
- Implement query result caching to reduce compute costs
- Monitor and optimize database query performance

## 🚀 Future Improvements (Additional Considerations)

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

