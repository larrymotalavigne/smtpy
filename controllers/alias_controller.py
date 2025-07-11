from fastapi import APIRouter, HTTPException
from typing import List, Optional
from database.db import get_session
from database.models import Alias

router = APIRouter()

@router.get("/aliases", response_model=List[dict])
def list_aliases(domain_id: Optional[int] = None):
    with get_session() as session:
        query = session.query(Alias)
        if domain_id:
            query = query.filter(Alias.domain_id == domain_id)
        return [alias.__dict__ for alias in query.all()]

@router.post("/aliases", response_model=dict)
def create_alias(alias: dict):
    with get_session() as session:
        db_alias = Alias(local_part=alias["local_part"], targets=alias["targets"], domain_id=alias["domain_id"])
        session.add(db_alias)
        session.commit()
        session.refresh(db_alias)
        return db_alias.__dict__

@router.get("/aliases/{alias_id}", response_model=dict)
def get_alias(alias_id: int):
    with get_session() as session:
        alias = session.get(Alias, alias_id)
        if not alias:
            raise HTTPException(status_code=404, detail="Alias not found")
        return alias.__dict__

@router.delete("/aliases/{alias_id}")
def delete_alias(alias_id: int):
    with get_session() as session:
        alias = session.get(Alias, alias_id)
        if not alias:
            raise HTTPException(status_code=404, detail="Alias not found")
        session.delete(alias)
        session.commit()
        return {"ok": True} 