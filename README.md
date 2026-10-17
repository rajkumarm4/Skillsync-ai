# SkillSync AI

**IBM Z Datathon 2026 | Event Code: SSF2026 | Category: Wildcard — Beyond the Obvious**

> An enterprise workforce intelligence engine that predicts skill gaps before they block projects,
> generates minimal targeted learning paths, and optimally allocates employees to projects —
> deployed on **IBM LinuxONE Community Cloud (s390x)**.

---

## 🚀 Live Demo

| Service | URL |
|---|---|
| API (Swagger Docs) | `http://<linuxone-ip>:8000/docs` |
| Dashboard | `http://<linuxone-ip>:8501` |
| Health Check | `http://<linuxone-ip>:8000/health` |

---

## 🏗️ Architecture

```
[ Streamlit Frontend :8501 ]
         │
         ▼
[ FastAPI REST API  :8000 ]  ←──►  [ PostgreSQL DB :5432 ]
         │                              │
         │                         Skill Graph
         │                         Employee Profiles
         │                         Project Registry
         │                         Audit Log (Z encrypted)
         ▼
[ AI Engine Layer ]
  ├── Skill Inference     (scikit-learn TF-IDF + cosine similarity)
  ├── Skill Gap Detector  (workforce coverage analysis)
  ├── Learning Path Gen   (minimal gap-targeted modules)
  └── Allocation Optimizer (Google OR-Tools CP-SAT solver)
         │
         ▼
[ IBM LinuxONE Community Cloud — Ubuntu 22.04 (s390x) ]
  • Pervasive encryption: data encrypted at rest by default
  • Native s390x: all Python libraries run without recompilation
  • Tamper-evident audit trail for every allocation decision
```

---

## 📂 Project Structure

```
skillsync-ai/
├── backend/
│   ├── main.py              # FastAPI app + audit middleware
│   ├── models.py            # SQLAlchemy ORM (5 tables)
│   ├── schemas.py           # Pydantic request/response models
│   ├── database.py          # DB connection
│   ├── seed_data.py         # 20 employees + 5 projects synthetic data
│   ├── routers/
│   │   ├── employees.py
│   │   ├── projects.py
│   │   ├── skills.py        # Gap detection + skill inference
│   │   └── allocation.py    # Learning paths + optimizer + simulation
│   └── engine/
│       ├── skill_inference.py   # TF-IDF skills taxonomy matching
│       ├── gap_detector.py      # Project vs workforce gap analysis
│       ├── learning_path.py     # Minimal module path generator
│       └── optimizer.py         # OR-Tools CP-SAT allocation engine
├── frontend/
│   └── app.py               # 6-page Streamlit dashboard
├── requirements.txt
├── docker-compose.yml
└── env.example
```

---

## ⚡ Quick Start (Local)

### Prerequisites
- Python 3.10+
- PostgreSQL 14+

### 1. Clone and install
```bash
git clone https://github.com/<your-username>/skillsync-ai.git
cd skillsync-ai
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp env.example .env
# Edit .env with your PostgreSQL credentials
```

### 3. Create the database
```sql
CREATE DATABASE skillsync_db;
CREATE USER skillsync WITH PASSWORD 'skillsync123';
GRANT ALL PRIVILEGES ON DATABASE skillsync_db TO skillsync;
```

### 4. Seed data
```bash
python backend/seed_data.py
```

### 5. Start the API
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Start the Dashboard
```bash
# In a separate terminal:
API_BASE=http://localhost:8000 streamlit run frontend/app.py --server.port 8501
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🐳 Docker Compose (Recommended)

```bash
docker-compose up --build
```

Services start on:
- Dashboard: http://localhost:8501
- API: http://localhost:8000/docs
- PostgreSQL: localhost:5432

---

## 🖥️ IBM LinuxONE Deployment

### Deploy to LinuxONE Community Cloud

1. Log in at [linuxone.cloud.marist.edu](https://linuxone.cloud.marist.edu)
2. Deploy Ubuntu 22.04 instance (m1.medium: 2 vCPU, 4 GB RAM)
3. SSH into your instance
4. Run the setup:

```bash
sudo apt update && sudo apt install -y python3.10 python3-pip postgresql postgresql-contrib git
git clone https://github.com/<your-username>/skillsync-ai.git
cd skillsync-ai
pip3 install -r requirements.txt

# Setup PostgreSQL
sudo -u postgres psql -c "CREATE DATABASE skillsync_db;"
sudo -u postgres psql -c "CREATE USER skillsync WITH PASSWORD 'skillsync123';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE skillsync_db TO skillsync;"

# Seed data
python3 backend/seed_data.py

# Start API (background)
nohup uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

# Start Dashboard (background)
nohup streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0 &
```

5. Open firewall ports 8000 and 8501
6. Verify: `curl http://localhost:8000/health`
   - Response should include `"platform": "LinuxONE s390x"`

---

## 🤖 AI Components

| Component | Technique | Purpose |
|---|---|---|
| Skill Inference | TF-IDF + Cosine Similarity | Extract skills from text descriptions |
| Gap Detector | Coverage analysis | Find critical workforce bottlenecks |
| Learning Path | Curated module catalog | Minimal upskilling path per employee |
| Optimizer | OR-Tools CP-SAT | Constrained multi-project assignment |

---

## 🔒 IBM Z Security Story

Workforce data is among the most sensitive enterprise data. On IBM LinuxONE:

- **Pervasive Encryption**: Employee assessments and skill profiles are encrypted at rest at hardware level — no application code required
- **Tamper-Evident Audit Trail**: Every allocation decision is logged with timestamp and user role, benefiting from Z's hardware integrity guarantees
- **Performance Density**: OR-Tools solver and scikit-learn models run natively on s390x via IBM AI Toolkit for Z

---

## 📊 Key Results (Demo Scenario)

- 20 employees, 5 projects
- **Critical bottleneck detected**: P1 (Legacy App Migration) needs 3 cloud engineers at proficiency ≥ 4, only 2 qualified — both overloaded
- **Optimizer improvement**: ~38% better skill coverage vs naive assignment
- **Reallocation latency**: < 500ms when project deadline changes
- **Upskilling**: Employee "Aisha Patel" (Python L5, Cloud L2) reaches cloud proficiency L4 in ~8 days via 4 targeted modules

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI, Python 3.10 |
| Database | PostgreSQL 14 |
| ORM | SQLAlchemy 2.0 |
| ML | scikit-learn (TF-IDF) |
| Optimizer | Google OR-Tools (CP-SAT) |
| Frontend | Streamlit, Plotly |
| Platform | IBM LinuxONE Community Cloud (Ubuntu 22.04, s390x) |

---

## 📋 Open Source Resources

1. FastAPI — https://github.com/tiangolo/fastapi
2. SQLAlchemy — https://github.com/sqlalchemy/sqlalchemy
3. scikit-learn — https://github.com/scikit-learn/scikit-learn
4. Google OR-Tools — https://github.com/google/or-tools
5. Streamlit — https://github.com/streamlit/streamlit
6. Plotly — https://github.com/plotly/plotly.py
7. LinuxONE Community Cloud — https://linuxone.cloud.marist.edu
8. IBM LinuxONE Fast Start Guides — https://community.ibm.com/zsystems/l1cc/faststart/

---

## License

MIT License — see [LICENSE](LICENSE)

---

*IBM Z Datathon 2026 | Event Code: SSF2026 | SkillSync AI*
