"""Business logic controller for forwarding rules."""

import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.alias import Alias
from shared.models.forwarding_rule import ForwardingRule, RuleConditionType, RuleActionType
from api.database import rules_database, aliases_database
from api.schemas.forwarding_rule import RuleCreate, RuleUpdate

logger = logging.getLogger(__name__)


async def create_forwarding_rule(
    session: AsyncSession,
    user_id: int,
    rule_data: RuleCreate
) -> tuple[ForwardingRule | None, str | None]:
    """
    Create a new forwarding rule.

    Args:
        session: Database session
        user_id: User ID (for authorization)
        rule_data: Rule creation data

    Returns:
        Tuple of (created rule, error message)
    """
    try:
        # Verify alias exists and belongs to user
        alias = await aliases_database.get_alias_by_id(session, rule_data.alias_id)
        if not alias:
            return None, "Alias not found"

        # Verify alias belongs to user's organization
        # TODO: Add proper authorization check with domain -> organization -> user

        # Convert string enums to actual enums
        try:
            condition_type = RuleConditionType[rule_data.condition_type]
            action_type = RuleActionType[rule_data.action_type]
        except KeyError as e:
            return None, f"Invalid enum value: {str(e)}"

        # Validate action_value for REDIRECT action
        if action_type == RuleActionType.REDIRECT and not rule_data.action_value:
            return None, "action_value is required for REDIRECT action type"

        # Create rule
        rule = await rules_database.create_rule(
            session=session,
            alias_id=rule_data.alias_id,
            name=rule_data.name,
            condition_type=condition_type,
            condition_value=rule_data.condition_value,
            action_type=action_type,
            action_value=rule_data.action_value,
            priority=rule_data.priority,
            description=rule_data.description,
        )

        return rule, None

    except Exception as e:
        logger.error(f"Error creating forwarding rule: {str(e)}")
        return None, f"Failed to create rule: {str(e)}"


async def get_rules_for_alias(
    session: AsyncSession,
    user_id: int,
    alias_id: int,
    active_only: bool = False
) -> tuple[List[ForwardingRule], str | None]:
    """
    Get all forwarding rules for an alias.

    Args:
        session: Database session
        user_id: User ID (for authorization)
        alias_id: Alias ID
        active_only: If True, only return active rules

    Returns:
        Tuple of (list of rules, error message)
    """
    try:
        # Verify alias exists and belongs to user
        alias = await aliases_database.get_alias_by_id(session, alias_id)
        if not alias:
            return [], "Alias not found"

        # TODO: Add proper authorization check

        rules = await rules_database.get_rules_by_alias(
            session=session,
            alias_id=alias_id,
            active_only=active_only
        )

        return rules, None

    except Exception as e:
        logger.error(f"Error fetching rules: {str(e)}")
        return [], f"Failed to fetch rules: {str(e)}"


async def get_rule_by_id(
    session: AsyncSession,
    user_id: int,
    rule_id: int
) -> tuple[ForwardingRule | None, str | None]:
    """
    Get a forwarding rule by ID.

    Args:
        session: Database session
        user_id: User ID (for authorization)
        rule_id: Rule ID

    Returns:
        Tuple of (rule, error message)
    """
    try:
        rule = await rules_database.get_rule_by_id(session, rule_id)
        if not rule:
            return None, "Rule not found"

        # TODO: Add proper authorization check

        return rule, None

    except Exception as e:
        logger.error(f"Error fetching rule: {str(e)}")
        return None, f"Failed to fetch rule: {str(e)}"


async def update_forwarding_rule(
    session: AsyncSession,
    user_id: int,
    rule_id: int,
    rule_data: RuleUpdate
) -> tuple[ForwardingRule | None, str | None]:
    """
    Update a forwarding rule.

    Args:
        session: Database session
        user_id: User ID (for authorization)
        rule_id: Rule ID
        rule_data: Rule update data

    Returns:
        Tuple of (updated rule, error message)
    """
    try:
        # Verify rule exists
        rule = await rules_database.get_rule_by_id(session, rule_id)
        if not rule:
            return None, "Rule not found"

        # TODO: Add proper authorization check

        # Convert string enums if provided
        condition_type = None
        action_type = None

        if rule_data.condition_type:
            try:
                condition_type = RuleConditionType[rule_data.condition_type]
            except KeyError:
                return None, f"Invalid condition_type: {rule_data.condition_type}"

        if rule_data.action_type:
            try:
                action_type = RuleActionType[rule_data.action_type]
            except KeyError:
                return None, f"Invalid action_type: {rule_data.action_type}"

        # Validate action_value for REDIRECT
        if action_type == RuleActionType.REDIRECT and not rule_data.action_value:
            return None, "action_value is required for REDIRECT action type"

        # Update rule
        updated_rule = await rules_database.update_rule(
            session=session,
            rule_id=rule_id,
            name=rule_data.name,
            condition_type=condition_type,
            condition_value=rule_data.condition_value,
            action_type=action_type,
            action_value=rule_data.action_value,
            priority=rule_data.priority,
            description=rule_data.description,
            is_active=rule_data.is_active,
        )

        return updated_rule, None

    except Exception as e:
        logger.error(f"Error updating rule: {str(e)}")
        return None, f"Failed to update rule: {str(e)}"


async def delete_forwarding_rule(
    session: AsyncSession,
    user_id: int,
    rule_id: int
) -> tuple[bool, str | None]:
    """
    Delete a forwarding rule.

    Args:
        session: Database session
        user_id: User ID (for authorization)
        rule_id: Rule ID

    Returns:
        Tuple of (success, error message)
    """
    try:
        # Verify rule exists
        rule = await rules_database.get_rule_by_id(session, rule_id)
        if not rule:
            return False, "Rule not found"

        # TODO: Add proper authorization check

        success = await rules_database.delete_rule(session, rule_id)
        return success, None

    except Exception as e:
        logger.error(f"Error deleting rule: {str(e)}")
        return False, f"Failed to delete rule: {str(e)}"


async def toggle_rule_active(
    session: AsyncSession,
    user_id: int,
    rule_id: int
) -> tuple[ForwardingRule | None, str | None]:
    """
    Toggle a rule's active status.

    Args:
        session: Database session
        user_id: User ID (for authorization)
        rule_id: Rule ID

    Returns:
        Tuple of (updated rule, error message)
    """
    try:
        # Verify rule exists
        rule = await rules_database.get_rule_by_id(session, rule_id)
        if not rule:
            return None, "Rule not found"

        # TODO: Add proper authorization check

        updated_rule = await rules_database.toggle_rule_status(session, rule_id)
        return updated_rule, None

    except Exception as e:
        logger.error(f"Error toggling rule status: {str(e)}")
        return None, f"Failed to toggle rule status: {str(e)}"
