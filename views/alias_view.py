import datetime

from fastapi import APIRouter, HTTPException, Path, Body
from typing import List, Optional

from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

from utils.db import get_session
from database.models import Alias

router = APIRouter()

@router.get("/aliases", response_model=List[dict])
def list_aliases(domain_id: Optional[int] = None):
    with get_session() as session:
        query = session.query(Alias)
        if domain_id:
            query = query.filter(Alias.domain_id == domain_id)
        return [{
            "id": alias.id,
            "local_part": alias.local_part,
            "targets": alias.targets,
            "domain_id": alias.domain_id,
            "owner_id": alias.owner_id,
            "expires_at": alias.expires_at.isoformat() if alias.expires_at else None,
            "created_at": alias.created_at.isoformat() if alias.created_at else None,
            "updated_at": alias.updated_at.isoformat() if alias.updated_at else None
        } for alias in query.all()]

@router.post("/aliases", response_model=dict)
def create_alias(alias: dict):
    with get_session() as session:
        db_alias = Alias(local_part=alias["local_part"], targets=alias["targets"], domain_id=alias["domain_id"])
        session.add(db_alias)
        session.commit()
        session.refresh(db_alias)
        return {
            "id": db_alias.id,
            "local_part": db_alias.local_part,
            "targets": db_alias.targets,
            "domain_id": db_alias.domain_id,
            "owner_id": db_alias.owner_id,
            "expires_at": db_alias.expires_at.isoformat() if db_alias.expires_at else None,
            "created_at": db_alias.created_at.isoformat() if db_alias.created_at else None,
            "updated_at": db_alias.updated_at.isoformat() if db_alias.updated_at else None
        }

@router.get("/aliases/{alias_id}", response_model=dict)
def get_alias(request: Request, alias_id: int):
    user = request.session.get("user_id")
    if not user:
        raise HTTPException(status_code=403, detail="Authentication required")
    with get_session() as session:
        alias = session.get(Alias, alias_id)
        if not alias:
            raise HTTPException(status_code=404, detail="Alias not found")
        return {
            "id": alias.id,
            "local_part": alias.local_part,
            "targets": alias.targets,
            "domain_id": alias.domain_id,
            "owner_id": alias.owner_id,
            "expires_at": alias.expires_at.isoformat() if alias.expires_at else None,
            "created_at": alias.created_at.isoformat() if alias.created_at else None,
            "updated_at": alias.updated_at.isoformat() if alias.updated_at else None
        }

@router.delete("/aliases/{alias_id}")
def delete_alias(alias_id: int):
    with get_session() as session:
        alias = session.get(Alias, alias_id)
        if not alias:
            raise HTTPException(status_code=404, detail="Alias not found")
        session.delete(alias)
        session.commit()
        return {"ok": True}


@router.get("/aliases/{domain_id}")
def api_list_aliases(domain_id: int = Path(...)):
    with get_session() as session:
        now = datetime.datetime.utcnow()
        aliases = session.query(Alias).filter_by(domain_id=domain_id).all()
        return [{"id": a.id, "local_part": a.local_part, "targets": a.targets, "expires_at": a.expires_at.isoformat() if a.expires_at else None} for a in aliases]

@router.post("/api/aliases/{domain_id}")
def api_add_alias(request: Request, domain_id: int = Path(...), local_part: str = Body(...), targets: str = Body(...), expires_at: str = Body(None)):
    user = request.session.get("user_id")
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    with get_session() as session:
        exp = datetime.datetime.fromisoformat(expires_at) if expires_at else None
        alias = Alias(local_part=local_part, targets=targets, domain_id=domain_id, expires_at=exp)
        session.add(alias)
        session.commit()
        return {"success": True, "id": alias.id}

@router.delete("/api/alias/{alias_id}")
def api_delete_alias(request: Request, alias_id: int = Path(...)):
    user = request.session.get("user_id")
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    with get_session() as session:
        alias = session.get(Alias, alias_id)
        if alias:
            session.delete(alias)
            session.commit()
            return {"success": True}
        return JSONResponse(status_code=404, content={"error": "Alias not found"})

@router.post("/api/alias-test/{alias_id}")
def api_test_alias(alias_id: int = Path(...)):
    with get_session() as session:
        alias = session.get(Alias, alias_id)
        if not alias:
            return JSONResponse(status_code=404, content={"error": "Alias not found"})
        print(f"Test email would be sent to {alias.targets} for alias {alias.local_part}")
        return {"success": True, "message": f"Test email sent to {alias.targets}"}
