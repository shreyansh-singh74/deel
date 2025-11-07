# Deel AI Challenge - Transaction Matching API

A FastAPI-based REST API that matches users to transactions using fuzzy string matching and finds similar transactions using sentence embeddings. Built with FastAPI and Sentence Transformers.

## Project Overview

This project provides **2 API endpoints**:
- `/match_users/{transaction_id}` - Matches users to transactions based on description similarity
- `/similar_transactions` - Finds semantically similar transactions using embeddings

**Tech Stack:** FastAPI, Sentence Transformers, RapidFuzz, Pandas

---

## Setup Instructions

### Step 1: Clone or Download the Repository

```bash
# Option A: Clone with Git
git clone <repository-url>
cd deel

# Option B: Download ZIP and extract
```

### Step 2: Create Virtual Environment

```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** First run may take 2-5 minutes to download the embedding model (~500MB).

### Step 4: Prepare Data Files

Place your CSV files in the `data/` folder:

**`data/transactions.csv`** (required columns: `id`, `description`)
```csv
id,description
RAZbbmLX,Transfer from Emma Brown for Deel
pXAMd74U,Payment cntr ref: Jack Cooper for Deel
```

**`data/users.csv`** (required columns: `id`, `name`)
```csv
id,name
BuCoIvL79A,Emma Brown
XSwFsQlyYa,James Bennett
```

### Step 5: Run the Server

```bash
uvicorn app.main:app --reload
```

The server will start at `http://127.0.0.1:8000`

**Access Interactive Docs:** http://127.0.0.1:8000/docs

---

## API Endpoints

### 1. Match Users to Transaction

**Endpoint:** `GET /match_users/{transaction_id}`

**Example Request:**
```bash
curl http://127.0.0.1:8000/match_users/RAZbbmLX
```

**Example Response:**
```json
{
  "users": [
    {
      "id": "BuCoIvL79A",
      "name": "Emma Brown",
      "match_metric": 95.5,
      "method": "fuzzy"
    }
  ],
  "total_number_of_matches": 1
}
```

**What it does:** Returns users that match the transaction description with confidence scores (0-100).

---

### 2. Find Similar Transactions

**Endpoint:** `POST /similar_transactions`

**Example Request:**
```bash
curl -X POST "http://127.0.0.1:8000/similar_transactions" \
     -H "Content-Type: application/json" \
     -d '{"query": "Payment from John for Deel"}'
```

**Example Response:**
```json
{
  "transactions": [
    {
      "id": "txn_456",
      "embedding": [0.123, 0.456, 0.789, ...]
    }
  ],
  "total_number_of_tokens_used": 5
}
```

**What it does:** Returns transactions with semantically similar descriptions using sentence embeddings.

---

## Approach / Methodology

### Task 1: Match Users to Transactions

**Approach:** Hybrid fuzzy matching + multilingual embeddings

1. **Fuzzy Matching (First Pass):**
   - Extracts potential names from transaction descriptions using anchor patterns ("from", "ref:", "for deel")
   - Uses RapidFuzz for fast string matching
   - Applies bonuses for name overlaps and penalties for secondary mentions (CC)
   - Accepts matches with score ≥ 70

2. **Embedding Fallback:**
   - If fuzzy matching fails, uses multilingual sentence embeddings
   - Transliterates non-Latin scripts (Chinese, Greek, Hebrew)
   - Computes cosine similarity with precomputed user embeddings
   - Accepts matches with cosine similarity ≥ 0.75

**Edge Cases Handled:**
-  Typos and misspellings
-  Non-Latin scripts (Chinese, Greek, Hebrew) with transliteration
-  Name order variations (Fisher Victoria → Victoria Fisher)
-  Glued words (matthewbrooks → matthew brooks)
-  Digits in names (kelly01 → kelly, 0→o, 1→l)
-  Multiple people (CC handling)
-  Noisy text and boilerplate removal
-  Case variations and diacritics
-  And 12+ more edge cases

---

### Task 2: Find Similar Transactions

**Approach:** Sentence embeddings with cosine similarity

1. Pre-computes embeddings for all transaction descriptions at startup
2. Encodes query text into embedding vector
3. Calculates cosine similarity between query and all transactions
4. Returns top 5 most similar transactions with their embedding vectors

**Model Used:** `all-MiniLM-L6-v2` (384-dimensional embeddings)

---

## Limitations

1. **Model Limitations:**
   - Small embedding model (MiniLM) may miss deeper semantic nuances
   - Very uncommon transliterations outside the provided map might have lower accuracy

2. **Matching Challenges:**
   - Severe typos or unusual abbreviations can confuse the matching
   - Names completely absent from descriptions will return empty results

3. **Scalability:**
   - Not optimized for large-scale datasets (>100k users) - uses in-memory storage
   - No pagination for large result sets
   - CSV-based storage not suitable for concurrent access in production

---

## Future Improvements / Production Plan

### Phase 1: Database & Storage
- **Replace CSV with PostgreSQL** for scalable, concurrent data storage
- **Add Vector Database** (FAISS or Pinecone) for fast similarity search at scale
- **Implement connection pooling** for database efficiency

### Phase 2: Performance & Scalability
- **Add Redis caching** for frequently accessed results and embeddings
- **Implement background jobs** (Celery) for async embedding computation
- **Add load balancing** (NGINX) for horizontal scaling
- **Containerize with Docker** for easy deployment

### Phase 3: Security & Reliability
- **Add API key authentication** and rate limiting
- **Implement structured logging** (JSON format) for debugging
- **Add monitoring** (Prometheus + Grafana) for metrics and alerts
- **Set up health checks** and auto-scaling

### Phase 4: Advanced Features
- **Model fine-tuning** on domain-specific transaction data
- **Batch processing API** for multiple transactions at once
- **API versioning** for backward compatibility
- **Hybrid search** (keyword + semantic) for better accuracy

### Deployment Options
- **AWS:** ECS + RDS + ElastiCache (managed services)
- **GCP:** Cloud Run + Cloud SQL + Memorystore
- **Kubernetes:** Full control with auto-scaling and self-healing

**Estimated Cost:** $50-200/month for small-medium scale (10k-100k users)

---

## 📦 Requirements

See `requirements.txt` for full list. Key dependencies:

- `fastapi==0.104.1` - Web framework
- `sentence-transformers>=2.3.0` - Embeddings
- `rapidfuzz==3.14.3` - Fuzzy matching
- `pandas==2.1.3` - Data manipulation
- `uvicorn[standard]==0.24.0` - ASGI server
- `unidecode>=1.3.7` - Text normalization
- `numpy>=1.24.0` - Numerical operations

**Model Used:** `paraphrase-multilingual-MiniLM-L12-v2` (for user matching)  
**Model Used:** `all-MiniLM-L6-v2` (for transaction similarity)

**Note:** First run downloads the models automatically (~500MB total). Subsequent runs use cached models.

---

## 🧪 Testing

```bash
# Run tests
pytest

# Or test manually via API
# Start server: uvicorn app.main:app --reload
# Visit: http://127.0.0.1:8000/docs
```

---

## 📚 Project Structure

```
deel/
├── app/
│   ├── main.py                    # FastAPI application
│   ├── config/                    # Configuration
│   ├── preprocessing/             # Text & user preprocessing
│   ├── matching/                  # Matching algorithms
│   └── routes/                    # API endpoints
├── data/                          # CSV data files
├── models/                        # Cached embeddings
├── requirements.txt               # Dependencies
└── README.md                      # This file
```

---

## 💡 Quick Tips

- **Interactive Docs:** Visit `/docs` for Swagger UI with try-it-out functionality
- **Health Check:** Use `/health` to verify server status
- **Cache:** Preprocessed user embeddings are cached in `models/users_enriched.pkl`
- **Configuration:** Adjust thresholds in `app/config/settings.py`

---

## 📝 License

MIT License

---

**Need Help?** Check the interactive docs at http://127.0.0.1:8000/docs when the server is running!
