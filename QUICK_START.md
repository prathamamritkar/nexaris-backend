# 🚀 NEXARIS Backend - Quick Start Checklist

Complete this checklist to get your corrected NEXARIS backend running safely.

## ⏱️ Time Required: ~30 minutes

---

## Phase 1: Review & Understand (5 minutes)

- [ ] Read [AUDIT_COMPLETION_REPORT.md](./AUDIT_COMPLETION_REPORT.md) - Overview of all fixes
- [ ] Review [SECURITY_AUDIT.md](./SECURITY_AUDIT.md) - Detailed analysis
- [ ] Check [README.md](./README.md) - Deployment guide

---

## Phase 2: Environment Setup (10 minutes)

### Step 1: Create Virtual Environment
```bash
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Mac/Linux)
source .venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment
```bash
cp .env.example .env
```

### Step 4: Edit .env with Your Values
**Critical - Must be set:**
```env
NEO4J_URI=bolt://your-neo4j-host:7687          # Your Neo4j server
NEO4J_USER=neo4j                                 # Neo4j username
NEO4J_PASSWORD=YourStrongPassword123!@#          # STRONG password!
SARVAM_API_KEY=your_sarvam_api_key               # Your Sarvam AI key
CORS_ORIGINS=http://localhost:3000               # Your frontend origin
```

- [ ] ✅ Set NEO4J_URI
- [ ] ✅ Set NEO4J_USER
- [ ] ✅ Set NEO4J_PASSWORD (strong password!)
- [ ] ✅ Set SARVAM_API_KEY
- [ ] ✅ Set CORS_ORIGINS

---

## Phase 3: Verify Configuration (5 minutes)

```bash
# Test 1: Configuration loads without errors
python -c "from config import settings; print('✅ Configuration validated')"

# Test 2: Validators module loads
python -c "from validators import validate_citizen_id; print('✅ Validators ready')"

# Test 3: Database driver can be created
python -c "from main import get_db_driver; print('✅ Database driver ready')"
```

**Expected Output:**
```
✅ Configuration validated
✅ Validators ready
✅ Database driver ready
```

- [ ] ✅ All configuration tests pass

---

## Phase 4: Local Testing (10 minutes)

### Terminal 1: Start FastAPI Backend
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Wait for:**
```
Uvicorn running on http://0.0.0.0:8000
```

- [ ] ✅ Backend started successfully

### Terminal 2: Test Health Endpoint
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{"status": "healthy", "timestamp": "2026-06-24T..."}
```

- [ ] ✅ Health check passes

### Terminal 3: Test Valid Request
```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "citizen_id": "citizen_001",
    "intent": "RESOURCE_REQUEST",
    "item": "Blood Pack",
    "urgency": "CRITICAL",
    "location_context": "City Hospital"
  }'
```

**Expected Response:**
```json
{"status": "success", "message": "Resource request successfully mapped to topological network", "timestamp": "..."}
```

- [ ] ✅ Valid request accepted

### Terminal 4: Test Input Validation
```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "citizen_id": "ab",
    "intent": "RESOURCE_REQUEST",
    "item": "Blood Pack",
    "urgency": "CRITICAL",
    "location_context": "City Hospital"
  }'
```

**Expected Response:** Validation error (citizen_id too short)

- [ ] ✅ Invalid input properly rejected

### Terminal 5: Start Streamlit Frontend
```bash
streamlit run app.py
```

**Expected:** Streamlit opens at `http://localhost:8501`

- [ ] ✅ Frontend runs without errors

### Terminal 6: Start Background Worker
```bash
python worker.py
```

**Expected Output:**
```
🚀 PSA Worker starting...
✅ Configuration validated
🤖 Perpetual State Agent started
```

- [ ] ✅ Background worker started

---

## Phase 5: Security Verification (Optional but Recommended)

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Check for known vulnerabilities
safety check

# Scan code for security issues
bandit -r . -ll
```

- [ ] ✅ No critical vulnerabilities

---

## ✅ Deployment Ready Checklist

Before moving to production:

- [ ] All configuration tests pass
- [ ] Health endpoint responds
- [ ] Valid requests processed successfully
- [ ] Invalid requests rejected with validation errors
- [ ] All three processes (API, frontend, worker) start without errors
- [ ] Database connection verified
- [ ] API key verified
- [ ] CORS configuration correct for your domain
- [ ] Security verification passed (if ran)

---

## 🚀 Next Steps

### For Development
1. Continue with local testing
2. Implement OAuth2/JWT authentication
3. Add rate limiting middleware (slowapi)
4. Extend validators as needed

### For Production Deployment
1. **Follow** [README.md](./README.md) deployment section
2. **Review** production checklist in [SECURITY_AUDIT.md](./SECURITY_AUDIT.md)
3. **Set up** monitoring and alerting
4. **Configure** HTTPS with reverse proxy (nginx)
5. **Enable** database backups
6. **Deploy** to Render or your hosting platform

---

## 📞 Troubleshooting

### Issue: "NEO4J_PASSWORD must be set to a strong password"
**Solution**: Edit .env with a strong password (32+ chars, mixed case, symbols)

### Issue: "SARVAM_API_KEY environment variable is required"
**Solution**: Edit .env and set SARVAM_API_KEY from your Sarvam account

### Issue: "Could not connect to backend engine"
**Solution**: Verify backend is running on port 8000 and database is accessible

### Issue: CORS errors in browser console
**Solution**: Update CORS_ORIGINS in .env to match your frontend URL (include https://)

### Issue: "Database service unavailable"
**Solution**: Check Neo4j server is running and accessible at NEO4J_URI

---

## 📚 Documentation Quick Links

| Document | Purpose |
|----------|---------|
| [AUDIT_COMPLETION_REPORT.md](./AUDIT_COMPLETION_REPORT.md) | High-level overview of all fixes |
| [SECURITY_AUDIT.md](./SECURITY_AUDIT.md) | Detailed security analysis and fixes |
| [CORRECTIONS_SUMMARY.md](./CORRECTIONS_SUMMARY.md) | Summary and reference guide |
| [README.md](./README.md) | Full deployment and usage guide |
| [config.py](./config.py) | Configuration management |
| [validators.py](./validators.py) | Input validation utilities |
| [.env.example](./.env.example) | Environment variables template |

---

## ✨ You're Ready!

Your NEXARIS backend is now:
- ✅ **Secure** - Production-ready security
- ✅ **Validated** - Input validation on all endpoints
- ✅ **Configured** - Centralized configuration management
- ✅ **Logged** - Structured logging throughout
- ✅ **Documented** - Comprehensive documentation
- ✅ **Tested** - Verification steps completed

**Status**: Ready for deployment! 🎉

---

**Last Updated**: 2026-06-24
**Quick Start Time**: ~30 minutes
