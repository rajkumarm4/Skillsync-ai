"""
SkillSync AI — FastAPI Application Entry Point
Deployed on IBM LinuxONE Community Cloud (s390x)
Event Code: SSF2026
"""
import os
import platform
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from backend.database import engine, SessionLocal
from backend import models
from backend.routers import employees, projects, skills, allocation

load_dotenv()

app = FastAPI(
    title="SkillSync AI",
    description=(
        "Enterprise Workforce Intelligence Engine — "
        "Predict skill gaps, generate learning paths, optimize project allocation. "
        "Deployed on IBM LinuxONE Community Cloud. "
        "Event Code: SSF2026"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Create all tables on first startup
@app.on_event("startup")
async def startup():
    models.Base.metadata.create_all(bind=engine)


# CORS — allow Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Audit Log Middleware ─────────────────────────────────────────────────────

@app.middleware("http")
async def audit_log_middleware(request: Request, call_next):
    """
    Log every request to the audit_logs table.
    On IBM Z this log benefits from hardware-level integrity guarantees.
    """
    # Determine role from API key header
    api_key   = request.headers.get("X-API-Key", "")
    mgr_key   = os.getenv("MANAGER_API_KEY", "manager-secret-key-2026")
    emp_key   = os.getenv("EMPLOYEE_API_KEY", "employee-secret-key-2026")

    if api_key == mgr_key:
        user_role = "manager"
    elif api_key == emp_key:
        user_role = "employee"
    else:
        user_role = "anonymous"

    response = await call_next(request)

    # Write audit record asynchronously (best-effort — don't fail the request)
    try:
        db = SessionLocal()
        log = models.AuditLog(
            endpoint=str(request.url.path),
            method=request.method,
            user_role=user_role,
            request_summary=f"Query: {str(request.url.query)[:200]}" if request.url.query else None,
            response_status=response.status_code,
            timestamp=datetime.utcnow(),
        )
        db.add(log)
        db.commit()
        db.close()
    except Exception:
        pass  # Never let audit failure break a real request

    return response


# ─── Routers ─────────────────────────────────────────────────────────────────

app.include_router(employees.router)
app.include_router(projects.router)
app.include_router(skills.router)
app.include_router(allocation.router)


# ─── Core Endpoints ──────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {
        "service": "SkillSync AI",
        "status": "running",
        "platform": f"LinuxONE s390x" if "s390x" in platform.machine() else platform.machine(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "event_code": "SSF2026",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    """
    Health check endpoint — used as proof-of-deployment screenshot for submission.
    When running on LinuxONE the architecture field will show 's390x'.
    """
    arch = platform.machine()
    return {
        "status": "ok",
        "platform": "LinuxONE s390x" if "s390x" in arch else f"dev ({arch})",
        "architecture": arch,
        "timestamp": datetime.utcnow().isoformat(),
        "event_code": "SSF2026",
    }


@app.get("/audit-log", tags=["Audit"])
def get_audit_log(limit: int = 50, db=None):
    """
    Returns recent audit log entries — demonstrates tamper-evident
    decision logging on IBM Z pervasive encryption storage.
    """
    from backend.database import get_db
    from fastapi import Depends
    db = SessionLocal()
    try:
        logs = (
            db.query(models.AuditLog)
            .order_by(models.AuditLog.timestamp.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id":              l.id,
                "endpoint":        l.endpoint,
                "method":          l.method,
                "user_role":       l.user_role,
                "request_summary": l.request_summary,
                "response_status": l.response_status,
                "timestamp":       l.timestamp.isoformat(),
            }
            for l in logs
        ]
    finally:
        db.close()
