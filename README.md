# NEXARIS Backend - Production-Ready Resource Orchestration Platform

## 🚀 Overview

NEXARIS is a secure, scalable backend for managing resource requests in critical supply chains. It includes:

- **FastAPI Backend** - RESTful API for resource ingestion and management
- **Streamlit Frontend** - User interface for submitting resource requests
- **Neo4j Graph Database** - Topological network storage
- **Perpetual State Agent (PSA)** - Background autonomic agent for request processing

## 🔐 Security First

This codebase has been hardened for production use:

- ✅ Input validation on all endpoints
- ✅ CORS properly configured (no wildcard origins)
- ✅ Security headers added
- ✅ Encrypted database connections
- ✅ Structured logging without sensitive data exposure
- ✅ Configuration validation on startup
- ✅ File upload validation with size limits

**See [SECURITY_AUDIT.md](./SECURITY_AUDIT.md) for detailed security improvements.**

## 📋 Setup & Configuration

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# For development/testing:
pip install -r requirements-dev.txt
```

### 2. Environment Variables

Copy and configure `.env.example` to `.env`:

```bash
cp .env.example .env
```

**Critical variables to set:**

```env
# Database (REQUIRED - Never use defaults in production!)
NEO4J_URI=bolt://your-neo4j-host:7687
NEO4J_USER=your_neo4j_username
NEO4J_PASSWORD=your_strong_password_here

# API Keys (REQUIRED)
SARVAM_API_KEY=your_sarvam_api_key_here

# CORS Origins (REQUIRED in production)
CORS_ORIGINS=https://yourfrontend.com,https://www.yourfrontend.com

# Optional: Logging level
LOG_LEVEL=INFO
```

**⚠️ IMPORTANT: Do NOT commit `.env` files to version control!**

### 3. Local Development

```bash
# Start FastAPI backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start Streamlit frontend
streamlit run app.py

# Start background worker (PSA) in another terminal
python worker.py
```

### 4. Testing

```bash
# Run all tests
pytest tests/ -v

# Test with coverage
pytest tests/ --cov=. --cov-report=html

# Test a specific endpoint
curl http://localhost:8000/health
```

## 🌐 Deployment

### Render Deployment

1. **Set Start Command** to:
   ```
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

2. **Set Environment Variables** in Render dashboard:
   - `NEO4J_URI`
   - `NEO4J_USER`
   - `NEO4J_PASSWORD`
   - `SARVAM_API_KEY`
   - `CORS_ORIGINS`
   - `LOG_LEVEL=INFO`

3. **Add Background Worker Service**:
   - Create a background worker with start command: `python worker.py`
   - Set same environment variables

### Production Checklist

- [ ] Database credentials are strong (min 32 characters)
- [ ] CORS_ORIGINS configured for your domain
- [ ] HTTPS enforced (HSTS headers)
- [ ] Secrets stored in environment, not code
- [ ] Logging configured for your infrastructure
- [ ] Database backups enabled
- [ ] Monitoring and alerting set up
- [ ] Rate limiting enabled
- [ ] Authentication/authorization implemented

## 📁 Project Structure

```
.
├── main.py                 # FastAPI backend (core engine)
├── app.py                  # Streamlit frontend
├── worker.py               # Background PSA worker
├── config.py               # Centralized configuration
├── validators.py           # Input validation utilities
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
├── Procfile               # Deployment configuration
├── .env.example           # Environment template
├── SECURITY_AUDIT.md      # Detailed security report
└── README.md              # This file
```

## 🔌 API Endpoints

### Health Check
```
GET /health
Response: {"status": "healthy", "timestamp": "..."}
```

### Ingest Resource Request
```
POST /api/v1/ingest
Body: {
  "citizen_id": "citizen_001",
  "intent": "RESOURCE_REQUEST",
  "item": "Blood Pack",
  "urgency": "CRITICAL",
  "location_context": "City Hospital"
}
Response: {"status": "success", "message": "..."}
```

### Audio Processing (STT)
```
POST /api/v1/ingest/audio
Body: FormData with audio file
Response: {"status": "success", "structured_payload": {...}}
```

### Get Graph State
```
GET /api/v1/graph-state
Response: {"network_state": [...], "total_records": N}
```

### Migrate Relationships
```
POST /api/v1/migrate
Response: {"status": "success", "message": "..."}
```

## 🐛 Troubleshooting

### Database Connection Fails

```
Error: "Failed to connect to Neo4j"
```

Check:
- `NEO4J_URI` is correct
- `NEO4J_USER` and `NEO4J_PASSWORD` are correct
- Neo4j server is running and accessible
- Network/firewall allows connection to port 7687

### API Key Errors

```
Error: "Sarvam API rejection"
```

Check:
- `SARVAM_API_KEY` is set and valid
- API key has the necessary permissions
- Sarvam API service is accessible

### CORS Errors

```
Error: "Access to XMLHttpRequest blocked by CORS policy"
```

Check:
- Your frontend domain is in `CORS_ORIGINS`
- Include full protocol (https://)
- No trailing slashes

## 📊 Monitoring

Key metrics to monitor:

- **API Response Time**: Track latency of endpoints
- **Error Rate**: Monitor 4xx and 5xx responses
- **Database Connections**: Active connections in pool
- **Background Agent Health**: PSA loop execution status
- **Memory Usage**: Watch for memory leaks in long-running processes
- **Disk Usage**: Monitor database size and logs

## 🔄 Updates & Maintenance

### Updating Dependencies

```bash
# Check for outdated packages
pip list --outdated

# Update specific package
pip install --upgrade package_name

# Update all (use caution!)
pip install --upgrade -r requirements.txt

# Save updated versions
pip freeze > requirements.txt
```

### Database Migrations

```bash
# Run migration endpoint
curl -X POST http://localhost:8000/api/v1/migrate
```

## 📞 Support & Contributing

For issues, questions, or contributions:

1. Check [SECURITY_AUDIT.md](./SECURITY_AUDIT.md) for known issues
2. Review error logs for detailed diagnostics
3. Verify configuration matches [.env.example](./.env.example)

## 📄 License

See LICENSE file for details.

---

**Last Updated**: 2026-06-24
**Status**: Production-Ready with Security Hardening
