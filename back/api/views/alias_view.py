from typing import List, Optional

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from back.api.controllers.alias_controller import (
    list_aliases,
    create_alias,
    get_alias,
    delete_alias,
    list_aliases_by_domain,
    test_alias,
)
from back.core.utils.db import adbDep
from back.core.utils.user import require_login

router = APIRouter(prefix="/alias")


class AliasCreate(BaseModel):
    local_part: str
    targets: str
    domain_id: int


@router.get("/", response_model=List[dict])
async def list_aliases_endpoint(domain_id: Optional[int] = None, db: adbDep = None):
    return await list_aliases(db, domain_id=domain_id)


@router.post("/", response_model=dict)
async def create_alias_endpoint(alias: AliasCreate, db: adbDep = None):
    return await create_alias(db, alias.local_part, alias.targets, alias.domain_id)


@router.get("/{alias_id}", response_model=dict)
async def get_alias_endpoint(request: Request, alias_id: int, db: adbDep = None):
    require_login(request)
    try:
        return await get_alias(db, alias_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Alias not found")


@router.get("/by_domain/{domain_id}")
async def api_list_aliases_endpoint(domain_id: int = Path(...), db: adbDep = None):
    return await list_aliases_by_domain(db, domain_id)


@router.delete("/by_alias/{alias_id}")
async def api_delete_alias_endpoint(request: Request, alias_id: int = Path(...), db: adbDep = None):
    user = require_login(request)
    ok = await delete_alias(db, alias_id)
    if ok:
        return {"success": True}
    return JSONResponse(status_code=404, content={"error": "Alias not found"})


@router.post("/test/{alias_id}")
async def api_test_alias_endpoint(alias_id: int = Path(...), db: adbDep = None):
    try:
        result = await test_alias(db, alias_id)
    except LookupError:
        return JSONResponse(status_code=404, content={"error": "Alias not found"})
    print(f"{result['message']}")
    return {"success": True, "message": result["message"]}
