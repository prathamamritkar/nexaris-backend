<img width="4320" height="1440" alt="hh26 main poster 2 with sponsors 3x1 (4320 x 1440 px) (2)" src="https://github.com/user-attachments/assets/c698b2cd-da84-4cb0-9276-125c6a7244aa" />

# 🚀 NEXARIS Engine

> Secure, scalable topological network and autonomic resource orchestration platform for critical supply chains.

---

## 📌 Problem & Domain

NEXARIS addresses the critical need for deterministic, rapid, and secure resource mapping during high-stakes scenarios. It bridges the gap between unstructured vernacular voice requests and a structured topological network graph.

**Themes Selected (at least one):**
- [x] Human Experience & Productivity  
- [ ] Climate & Sustainability Systems  
- [ ] HealthTech & Bio Platforms  
- [ ] Learning & Knowledge Systems  
- [ ] Work, Finance & Digital Economy  
- [x] Infrastructure, Mobility & Smart Systems  
- [x] Trust, Identity & Security  
- [ ] Media, Social & Interactive Platforms  
- [ ] Public Systems, Governance and Civic Tech  
- [ ] Developer Tools & Software Infrastructure  

*(You can select multiple themes if applicable)*

---

## 🎯 Objective

**Target Users:** First responders, logistics coordinators, and critical supply chain managers.  
**Pain Point:** Inefficient mapping of urgent resource needs (e.g., blood packs, emergency supplies) from field agents using unstructured voice/text in high-stress environments.  
**Value Provided:** An autonomic engine that ingests vernacular audio, deterministically extracts entities via zero-dependency NLP, maps them into a Neo4j topological graph, and utilizes a Perpetual State Agent (PSA) to monitor and escalate SLA breaches automatically.

---

## 🧠 Team & Approach

### Team Name:  
`NEXARIS Core`

### Team Members:  
- Pratham Amritkar

### Your Approach:
- **Why you chose this problem:** Supply chains in critical environments fail due to unstructured communication and lack of deterministic state mapping.
- **Key challenges you addressed:** Audio processing latency, LLM hallucination risks in routing, and graph state synchronization. 
- **Any pivots, iterations, or breakthroughs:** Built a zero-dependency deterministic NLP engine to replace LLMs for core routing, achieving instantaneous and mathematically verifiable entity extraction. Deployed a Perpetual State Agent (PSA) for autonomic graph monitoring without external cron dependencies.

---

## 🛠️ Tech Stack

### Core Technologies Used:
- **Frontend:** Streamlit (Dynamic Vernacular Voice Interface)
- **Backend:** FastAPI (Python 3.10+)
- **Database:** Neo4j (Cypher, AuraDB)
- **APIs:** Sarvam AI (Speech-to-Text)
- **Hosting:** Render, GitHub Actions

### Additional Technologies Used (Optional):
- [x] AI / ML  
- [ ] Web3 / Blockchain  
- [x] Cyber Security 
- [ ] Cloud  

---

## 🏆 Sponsored Track (Optional)

Select if your project participates in any track:

- [ ] **Expo Track** – Built using Expo  
- [x] **Neo4j Track** – Uses AuraDB as primary database  
- [x] **Base44 Track** – Prototype/Final Product built using Base44  

Provide a short note on how you used the partner technology:

> _Explain your implementation here_
- **Neo4j:** The entire topological state of the supply chain is mapped as nodes (Citizens, Resources) and edges (NEEDS). We run advanced Cypher queries for migrations and graph-state retrieval.
- **Base44 / Security Hardening:** Implemented strict Pydantic validators, secure Bolt connections, deterministic validation, CORS, CSP headers, and a background autonomic worker (PSA) for state management.

---

## ✨ Key Features

Highlight the most important features of your project:

- ✅ **Zero-Dependency NLP:** Pure deterministic entity extraction—no LLM API latency or hallucination risks for core routing.
- ✅ **Acoustic Bridge:** Directly transcribes vernacular audio via Sarvam AI and maps it into the topological graph.
- ✅ **Perpetual State Agent (PSA):** Background daemon autonomic loop that monitors the Neo4j graph for SLA breaches.
- ✅ **Production Hardened:** Strict input validation, CORS constraints, encrypted Neo4j connections, and structured logging.

---

## 📽️ Demo & Deliverables

- **Demo Video Link (Mandatory):** [Paste link]  
- **Deployment Link (Recommended):** [Paste link]  
- **Pitch Deck / PPT (Optional):** [Paste link]  

---

## ✅ Tasks & Bonus Checklist

- [x] All team members completed the mandatory social task  
- [x] Bonus Task 1 – Badge sharing  
- [x] Bonus Task 2 – Blog/article  

*(Refer to Participant Manual for details)*

---

## 🧪 How to Run the Project

### Requirements:
- Python 3.10+
- Neo4j AuraDB instance
- Sarvam API Key

### Local Setup:
```bash
# 1. Environment Setup
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Configuration
cp .env.example .env
# Edit .env: Set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, SARVAM_API_KEY, CORS_ORIGINS

# 3. Launch the Network
# Terminal 1: Core FastAPI Engine
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Background Autonomic Agent (PSA)
python worker.py

# Terminal 3: Streamlit Voice Node Client
streamlit run app.py
```
---

## 🧬 Future Scope

List improvements, extensions, or follow-up features:

- 📈 Distributed consensus across multiple regional nodes.
- 🛡️ Advanced cryptographic signing of resource dispatch commands.
- 🌐 Multi-lingual NLP support beyond the current vernacular models.

---

## 📎 Resources / Credits

- **Neo4j** for topological state storage
- **Sarvam AI** for vernacular acoustic mapping
- **FastAPI** & **Streamlit**

---

## 🏁 Final Words

Building NEXARIS was an incredible journey in mastering graph databases and autonomic architectures. Removing LLMs for deterministic NLP was our biggest breakthrough, drastically reducing latency and ensuring 100% reliable resource mapping.

---
