"""Database operations for forwarding rules."""

import logging
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.forwarding_rule import ForwardingRule

logger = logging.getLogger(__name__)


async def create_rule(
    session: AsyncSession,
    alias_id: int,
    name: str,
    condition_type: str,
    condition_value: str,
    action_type: str,
    action_value: Optional[str] = None,
    priority: int = 100,
    description: Optional[str] = None,
) -> ForwardingRule:
    """
    Create a new forwarding rule.

    Args:
        session: Database session
        alias_id: Alias ID
        name: Rule name
        condition_type: Condition type (enum value)
        condition_value: Condition value
        action_type: Action type (enum value)
        action_value: Action value (for REDIRECT)
        priority: Rule priority (lower = evaluated first)
        description: Optional description

    Returns:
        Created forwarding rule
    """
    rule = ForwardingRule(
        alias_id=alias_id,
        name=name,
        condition_type=condition_type,
        condition_value=condition_value,
        action_type=action_type,
        action_value=action_value,
        priority=priority,
        description=description,
        is_active=True,
        match_count=0,
    )

    session.add(rule)
    await session.commit()
    await session.refresh(rule)

    logger.info(f"Created forwarding rule {rule.id} for alias {alias_id}")
    return rule


async def get_rule_by_id(session: AsyncSession, rule_id: int) -> Optional[ForwardingRule]:
    """
    Get forwarding rule by ID.

    Args:
        session: Database session
        rule_id: Rule ID

    Returns:
        Forwarding rule or None if not found
    """
    result = await session.execute(
        select(ForwardingRule).where(ForwardingRule.id == rule_id)
    )
    return result.scalar_one_or_none()


async def get_rules_by_alias(
    session: AsyncSession, alias_id: int, active_only: bool = False
) -> List[ForwardingRule]:
    """
    Get all forwarding rules for an alias.

    Args:
        session: Database session
        alias_id: Alias ID
        active_only: If True, only return active rules

    Returns:
        List of forwarding rules
    """
    query = select(ForwardingRule).where(ForwardingRule.alias_id == alias_id)

    if active_only:
        query = query.where(ForwardingRule.is_active == True)

    query = query.order_by(ForwardingRule.priority.asc(), ForwardingRule.created_at.asc())

    result = await session.execute(query)
    return list(result.scalars().all())


async def update_rule(
    session: AsyncSession,
    rule_id: int,
    name: Optional[str] = None,
    condition_type: Optional[str] = None,
    condition_value: Optional[str] = None,
    action_type: Optional[str] = None,
    action_value: Optional[str] = None,
    priority: Optional[int] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> Optional[ForwardingRule]:
    """
    Update a forwarding rule.

    Args:
        session: Database session
        rule_id: Rule ID
        name: New rule name
        condition_type: New condition type
        condition_value: New condition value
        action_type: New action type
        action_value: New action value
        priority: New priority
        description: New description
        is_active: New active status

    Returns:
        Updated forwarding rule or None if not found
    """
    rule = await get_rule_by_id(session, rule_id)
    if not rule:
        return None

    if name is not None:
        rule.name = name
    if condition_type is not None:
        rule.condition_type = condition_type
    if condition_value is not None:
        rule.condition_value = condition_value
    if action_type is not None:
        rule.action_type = action_type
    if action_value is not None:
        rule.action_value = action_value
    if priority is not None:
        rule.priority = priority
    if description is not None:
        rule.description = description
    if is_active is not None:
        rule.is_active = is_active

    await session.commit()
    await session.refresh(rule)

    logger.info(f"Updated forwarding rule {rule_id}")
    return rule


async def delete_rule(session: AsyncSession, rule_id: int) -> bool:
    """
    Delete a forwarding rule.

    Args:
        session: Database session
        rule_id: Rule ID

    Returns:
        True if deleted, False if not found
    """
    rule = await get_rule_by_id(session, rule_id)
    if not rule:
        return False

    await session.delete(rule)
    await session.commit()

    logger.info(f"Deleted forwarding rule {rule_id}")
    return True


async def toggle_rule_status(
    session: AsyncSession, rule_id: int
) -> Optional[ForwardingRule]:
    """
    Toggle a rule's active status.

    Args:
        session: Database session
        rule_id: Rule ID

    Returns:
        Updated rule or None if not found
    """
    rule = await get_rule_by_id(session, rule_id)
    if not rule:
        return None

    rule.is_active = not rule.is_active
    await session.commit()
    await session.refresh(rule)

    logger.info(f"Toggled rule {rule_id} active status to {rule.is_active}")
    return rule
