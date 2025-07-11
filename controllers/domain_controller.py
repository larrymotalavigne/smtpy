from fastapi import APIRouter, HTTPException
from typing import List, Optional
from database.db import get_session
from database.models import Domain

router = APIRouter()

@router.get("/domains", response_model=List[dict])
def list_domains():
    with get_session() as session:
        domains = session.query(Domain).all()
        return [domain.__dict__ for domain in domains]

@router.post("/domains", response_model=dict)
def create_domain(domain: dict):
    with get_session() as session:
        db_domain = Domain(name=domain["name"], catch_all=domain.get("catch_all"))
        session.add(db_domain)
        session.commit()
        session.refresh(db_domain)
        return db_domain.__dict__

@router.get("/domains/{domain_id}", response_model=dict)
def get_domain(domain_id: int):
    with get_session() as session:
        domain = session.get(Domain, domain_id)
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")
        return domain.__dict__

@router.delete("/domains/{domain_id}")
def delete_domain(domain_id: int):
    with get_session() as session:
        domain = session.get(Domain, domain_id)
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")
        session.delete(domain)
        session.commit()
        return {"ok": True} 