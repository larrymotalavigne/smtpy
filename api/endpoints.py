from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from config.db import get_session
from config.models import Domain, Alias

router = APIRouter()

# Pydantic schemas
class AliasSchema(BaseModel):
    id: int
    local_part: str
    target: str
    domain_id: int
    class Config:
        orm_mode = True

class AliasCreateSchema(BaseModel):
    local_part: str
    target: str
    domain_id: int

class DomainSchema(BaseModel):
    id: int
    name: str
    catch_all: Optional[str]
    aliases: List[AliasSchema] = []
    class Config:
        orm_mode = True

class DomainCreateSchema(BaseModel):
    name: str
    catch_all: Optional[str] = None

# Domain endpoints
@router.get("/domains", response_model=List[DomainSchema])
def list_domains():
    with get_session() as session:
        domains = session.query(Domain).all()
        return domains

@router.post("/domains", response_model=DomainSchema)
def create_domain(domain: DomainCreateSchema):
    with get_session() as session:
        db_domain = Domain(name=domain.name, catch_all=domain.catch_all)
        session.add(db_domain)
        session.commit()
        session.refresh(db_domain)
        return db_domain

@router.get("/domains/{domain_id}", response_model=DomainSchema)
def get_domain(domain_id: int):
    with get_session() as session:
        domain = session.get(Domain, domain_id)
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")
        return domain

@router.delete("/domains/{domain_id}")
def delete_domain(domain_id: int):
    with get_session() as session:
        domain = session.get(Domain, domain_id)
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")
        session.delete(domain)
        session.commit()
        return {"ok": True}

# Alias endpoints
@router.get("/aliases", response_model=List[AliasSchema])
def list_aliases(domain_id: Optional[int] = None):
    with get_session() as session:
        query = session.query(Alias)
        if domain_id:
            query = query.filter(Alias.domain_id == domain_id)
        return query.all()

@router.post("/aliases", response_model=AliasSchema)
def create_alias(alias: AliasCreateSchema):
    with get_session() as session:
        db_alias = Alias(local_part=alias.local_part, target=alias.target, domain_id=alias.domain_id)
        session.add(db_alias)
        session.commit()
        session.refresh(db_alias)
        return db_alias

@router.get("/aliases/{alias_id}", response_model=AliasSchema)
def get_alias(alias_id: int):
    with get_session() as session:
        alias = session.get(Alias, alias_id)
        if not alias:
            raise HTTPException(status_code=404, detail="Alias not found")
        return alias

@router.delete("/aliases/{alias_id}")
def delete_alias(alias_id: int):
    with get_session() as session:
        alias = session.get(Alias, alias_id)
        if not alias:
            raise HTTPException(status_code=404, detail="Alias not found")
        session.delete(alias)
        session.commit()
        return {"ok": True} 