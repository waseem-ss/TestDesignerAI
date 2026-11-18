# PHASE B: REST API & WEB UI - STARTUP GUIDE

## ✅ What's Included

### **1. FastAPI REST Interface** (`api.py`)
- Production-ready REST API
- Automatic failover with provider health tracking
- Batch processing support
- Real-time statistics
- OpenAPI documentation (Swagger UI)

### **2. Streamlit Dashboard** (`dashboard.py`)
- Interactive web UI
- Real-time requirement processing
- Provider health visualization
- Analytics & statistics
- Settings management

### **3. Docker Support** (Optional)
- Containerized deployment
- Multi-container setup (API + Dashboard)

---

## 🚀 Quick Start (3 steps)

### **Step 1: Install Dependencies**
```bash
cd TestDesignerAI
pip install -r requirements.txt
```

### **Step 2: Start the API Server**
```bash
# In terminal 1
python -m api.api
# or
python -m uvicorn api.api:app --host 0.0.0.0 --port 8000 --reload
```

**Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     API documentation available at http://localhost:8000/docs
```

### **Step 3: Start the Dashboard**
```bash
# In terminal 2
streamlit run frontend/dashboard.py
```

**Output:**
```
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
  Network URL: http://<your-ip>:8501
```

---

## 📱 Using the System

### **API Usage Examples**

#### **1. Process Single Requirement**
```bash
curl -X POST "http://localhost:8000/api/process" \
  -H "Content-Type: application/json" \
  -d '{
    "req_id": "REQ_001",
    "text": "The system shall authenticate users using OAuth 2.0",
    "task_type": "extraction"
  }'
```

#### **2. Check Provider Health**
```bash
curl http://localhost:8000/api/health
```

#### **3. Get Statistics**
```bash
curl http://localhost:8000/api/stats
```

#### **4. Batch Processing**
```bash
curl -X POST "http://localhost:8000/api/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": [
      {
        "req_id": "REQ_001",
        "text": "Requirement 1",
        "task_type": "extraction"
      },
      {
        "req_id": "REQ_002",
        "text": "Requirement 2",
        "task_type": "classification"
      }
    ]
  }'
```

### **Web Dashboard Usage**

1. **Open Browser:** `http://localhost:8501`
2. **Process Tab:** Enter requirements and process
3. **Analytics Tab:** View statistics and provider status
4. **Health Tab:** Monitor provider health in real-time
5. **Settings Tab:** Configure LLM parameters

---

## 🔧 Configuration

### **Environment Variables (.env)**

```bash
# Groq Configuration (Phase A)
GROQ_API_KEY=your_groq_key_here
GROQ_MODEL=mixtral-8x7b-32768

# Optional: OpenAI
OPENAI_API_KEY=your_openai_key_here

# Optional: Anthropic Claude
ANTHROPIC_API_KEY=your_claude_key_here

# Optional: Google Gemini
GOOGLE_API_KEY=your_gemini_key_here

# Local Ollama (default)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true
```

---

## 📊 API Endpoints

### **Core Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root info |
| POST | `/api/process` | Process single requirement |
| POST | `/api/batch` | Batch processing |
| GET | `/api/health` | Provider health status |
| GET | `/api/stats` | Usage statistics |
| GET | `/api/providers` | List available providers |
| GET | `/health` | Health check (load balancers) |

### **Documentation**
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 🏥 Health Monitoring

The system automatically tracks provider health:

```
Provider Status:
✅ Ollama (Local)         → 2 consecutive successes
✅ Groq (Cloud)          → 5 consecutive successes  
⚠️  OpenAI (Cloud)       → 1 error
❌ Claude (Cloud)        → 3+ errors (marked unhealthy)
⚠️  Gemini (Cloud)       → 2 errors
```

**Failover Logic:**
- If a provider fails, automatically switches to next available
- Tracks response times for optimization
- Re-tests unhealthy providers periodically
- Logs all failures for debugging

---

## 📈 Performance Tips

### **For Best Performance:**

1. **Use Groq for speed** (100x faster than CPU Ollama)
   - Set `GROQ_API_KEY` to enable
   - Most requests use Groq if available

2. **Keep Ollama running** for local fallback
   - No API key needed
   - No network latency
   - Privacy-preserving

3. **Monitor health regularly**
   - Check `/api/health` before high-load periods
   - Verify provider availability

4. **Enable caching** (if configured)
   - Reduces redundant API calls
   - Faster response times

---

## 🧪 Testing

### **Test Endpoints**
```bash
# 1. Health Check
curl http://localhost:8000/health
# Expected: {"status": "healthy"}

# 2. Provider Status
curl http://localhost:8000/api/health
# Shows all provider states

# 3. Statistics
curl http://localhost:8000/api/stats
# Shows usage metrics

# 4. Single Processing
curl -X POST http://localhost:8000/api/process \
  -H "Content-Type: application/json" \
  -d '{"req_id":"TEST_001","text":"Test requirement","task_type":"extraction"}'
```

---

## 🐛 Troubleshooting

### **API Won't Start**
```bash
# Check port 8000 is available
lsof -i :8000

# Use different port
python -m uvicorn api.api:app --port 8001
```

### **Dashboard Connection Issues**
1. Ensure API is running on `http://localhost:8000`
2. Check firewall settings
3. Try `http://127.0.0.1:8000` if localhost fails

### **Provider Failover Not Working**
```bash
# Check environment variables
echo $GROQ_API_KEY
echo $OLLAMA_URL

# Verify Ollama is running
curl http://localhost:11434/api/tags

# Test API health
curl http://localhost:8000/api/health
```

### **Slow Responses**
1. Check which provider is being used (see health endpoint)
2. Groq should be fastest
3. Local Ollama might be slow on CPU
4. Consider GPU acceleration for Ollama

---

## 📦 Deployment Options

### **Option 1: Local Development** ✅
```bash
# Terminal 1: API
python -m api.api

# Terminal 2: Dashboard  
streamlit run frontend/dashboard.py
```

### **Option 2: Docker** (Coming soon)
```bash
docker-compose up
# API: http://localhost:8000
# Dashboard: http://localhost:8501
```

### **Option 3: Production (Gunicorn + Nginx)**
```bash
gunicorn -w 4 -b 0.0.0.0:8000 api:app
```

---

## 📝 Example Workflow

### **1. Send Requirement via API**
```bash
curl -X POST "http://localhost:8000/api/process" \
  -H "Content-Type: application/json" \
  -d '{
    "req_id": "REQ_LOGIN_001",
    "text": "The system shall provide OAuth 2.0 authentication with single sign-on",
    "task_type": "extraction"
  }'
```

### **2. Check Health**
```bash
curl http://localhost:8000/api/health | jq
```

### **3. View Stats**
```bash
curl http://localhost:8000/api/stats | jq
```

### **4. Use Dashboard**
- Open http://localhost:8501
- Select task type
- Paste requirement
- Click Process
- Download results

---

## ✅ Verification Checklist

Before considering Phase B complete:

- [ ] API starts without errors
- [ ] API documentation visible at `/docs`
- [ ] Dashboard loads in browser
- [ ] Provider health shows in API
- [ ] Can process a test requirement
- [ ] Stats endpoint returns data
- [ ] Failover works (test by disabling Ollama)
- [ ] Dashboard displays results
- [ ] Can download results as JSON/CSV

---

## 🎯 What's Next?

### **Phase B Extensions (Optional):**
- [ ] Database caching (SQLite)
- [ ] User authentication
- [ ] API rate limiting
- [ ] Result export to PDF
- [ ] Advanced analytics dashboard
- [ ] Provider cost tracking
- [ ] Model performance comparison

### **Phase C (Future):**
- [ ] Fine-tuning pipeline
- [ ] Custom model integration
- [ ] Team collaboration features
- [ ] Enterprise deployment
- [ ] Research paper generation

---

## 📞 Support

- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/health
- **Dashboard:** http://localhost:8501
- **GitHub Issues:** (when you push the code)

---

**Ready to start Phase B?** Run the Quick Start commands above! 🚀
