"""
FastAPI REST API Server for Saps Iii Icu Mortality.
"""
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.responses import FileResponse
from pathlib import Path
from saps3_calc import calculate_metrics
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Saps Iii Icu Mortality API",
    description="SAPS 3 global hospital-mortality conversion, plus a legacy demonstration audit API (not for patient triage).",
    version="3.1.0",
)


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)


class MortalityRequest(BaseModel):
    saps3_score: int = Field(strict=True, ge=0, le=217, description="Precomputed SAPS 3 admission score")


@app.get("/", include_in_schema=False)
def homepage():
    return FileResponse(Path(__file__).resolve().parent.parent / "index.html")


@app.post("/api/mortality", summary="Estimate hospital mortality using the global SAPS 3 equation")
def api_mortality(payload: MortalityRequest):
    return calculate_metrics(saps3_score=payload.saps3_score)


@app.get("/health")
def health():
    return {"status": "ok", "service": "saps-iii-icu-mortality", "version": "3.1.0"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "demonstration-in-memory"
    }


@app.post("/api/audit", deprecated=True, summary="Legacy threshold demonstration (not clinical SAPS 3)")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat", deprecated=True, summary="Legacy mock chat demonstration")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
