"""API endpoints for forwarding rules."""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.user import User
from shared.core.db import get_db
from .auth_view import get_current_user
from api.controllers import rules_controller
from api.schemas.forwarding_rule import (
    RuleCreate,
    RuleUpdate,
    RuleResponse,
    RuleListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rules", tags=["rules"])


@router.post("", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    rule_data: RuleCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new forwarding rule.

    Requires authentication.
    """
    rule, error = await rules_controller.create_forwarding_rule(
        session=session,
        user_id=current_user.id,
        rule_data=rule_data,
    )

    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return rule


@router.get("/alias/{alias_id}", response_model=RuleListResponse)
async def get_rules_by_alias(
    alias_id: int,
    active_only: bool = False,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all forwarding rules for an alias.

    Requires authentication.
    """
    rules, error = await rules_controller.get_rules_for_alias(
        session=session,
        user_id=current_user.id,
        alias_id=alias_id,
        active_only=active_only,
    )

    if error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error)

    return {"rules": rules, "total": len(rules)}


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a forwarding rule by ID.

    Requires authentication.
    """
    rule, error = await rules_controller.get_rule_by_id(
        session=session,
        user_id=current_user.id,
        rule_id=rule_id,
    )

    if error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error)

    return rule


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: int,
    rule_data: RuleUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a forwarding rule.

    Requires authentication.
    """
    rule, error = await rules_controller.update_forwarding_rule(
        session=session,
        user_id=current_user.id,
        rule_id=rule_id,
        rule_data=rule_data,
    )

    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a forwarding rule.

    Requires authentication.
    """
    success, error = await rules_controller.delete_forwarding_rule(
        session=session,
        user_id=current_user.id,
        rule_id=rule_id,
    )

    if error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error)

    return None


@router.post("/{rule_id}/toggle", response_model=RuleResponse)
async def toggle_rule(
    rule_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Toggle a rule's active status.

    Requires authentication.
    """
    rule, error = await rules_controller.toggle_rule_active(
        session=session,
        user_id=current_user.id,
        rule_id=rule_id,
    )

    if error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error)

    return rule
