"""Mock cloud IAM service for simulating credential-revocation actions."""
from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="Mock Cloud IAM")

# In-memory token store for the lab.
_tokens: dict[str, bool] = {}


@app.post("/api/revoke")
def revoke(user: str) -> dict:
    _tokens[user] = False
    return {"user": user, "active": False}


@app.get("/api/status")
def status(user: str) -> dict:
    return {"user": user, "active": _tokens.get(user, True)}
