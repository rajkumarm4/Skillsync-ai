#!/bin/bash
# SkillSync AI — IBM LinuxONE Community Cloud Deployment Script
# Event Code: SSF2026
# Run this on your LinuxONE Ubuntu 22.04 (s390x) instance

set -e

echo "=== SkillSync AI — LinuxONE Setup ==="
echo "Architecture: $(uname -m)"
echo "Event Code: SSF2026"
echo ""

# 1. System packages
sudo apt-get update -y
sudo apt-get install -y python3.10 python3-pip python3.10-venv postgresql postgresql-contrib git ufw

# 2. PostgreSQL setup
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo -u postgres psql -c "CREATE DATABASE skillsync_db;" 2>/dev/null || echo "DB already exists"
sudo -u postgres psql -c "CREATE USER skillsync WITH PASSWORD 'skillsync123';" 2>/dev/null || echo "User already exists"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE skillsync_db TO skillsync;" 2>/dev/null || true

# 3. Clone repo (replace with your GitHub URL)
cd ~
if [ ! -d "skillsync-ai" ]; then
    git clone https://github.com/YOUR_USERNAME/skillsync-ai.git
fi
cd skillsync-ai

# 4. Python environment
python3.10 -m venv venv
source venv/bin/activate

# 5. Install dependencies (all packages have s390x wheels)
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Dependencies installed on $(uname -m)"
echo "   scikit-learn, OR-Tools, FastAPI, Streamlit all run natively on LinuxONE s390x"
echo ""

# 6. Configure environment
cat > .env << 'EOF'
DATABASE_URL=postgresql://skillsync:skillsync123@localhost:5432/skillsync_db
MANAGER_API_KEY=manager-secret-key-2026
EMPLOYEE_API_KEY=employee-secret-key-2026
APP_ENV=production
EOF

# 7. Seed database
python backend/seed_data.py

# 8. Open firewall ports
sudo ufw allow 8000/tcp
sudo ufw allow 8501/tcp

# 9. Start API (background)
nohup uvicorn backend.main:app --host 0.0.0.0 --port 8000 > /tmp/api.log 2>&1 &
echo "API started (PID $!)"
sleep 3

# 10. Verify API is running
echo ""
echo "=== Health Check ==="
curl -s http://localhost:8000/health | python3 -m json.tool
echo ""

# 11. Start Streamlit (background)
nohup streamlit run frontend/app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    > /tmp/streamlit.log 2>&1 &
echo "Dashboard started (PID $!)"

echo ""
echo "=== Deployment Complete ==="
PUBIP=$(curl -s ifconfig.me 2>/dev/null || echo "<your-public-ip>")
echo "API:       http://${PUBIP}:8000/docs"
echo "Dashboard: http://${PUBIP}:8501"
echo "Health:    http://${PUBIP}:8000/health"
echo ""
echo "IMPORTANT: Take a screenshot of the health endpoint response for your submission."
echo "It should show: 'platform': 'LinuxONE s390x'"
echo ""
echo "Event Code: SSF2026"
