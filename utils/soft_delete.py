"""Soft delete utilities for SMTPy."""

from datetime import datetime
from typing import Type, TypeVar, Optional

from sqlalchemy.orm import Session

from database.models import Base, User, Domain, Alias

T = TypeVar("T", bound=Base)


def soft_delete(session: Session, model_instance: T) -> T:
    """
    Soft delete a model instance by setting is_deleted=True and deleted_at=now().

    Args:
        session: SQLAlchemy session
        model_instance: The model instance to soft delete

    Returns:
        The updated model instance
    """
    model_instance.is_deleted = True
    model_instance.deleted_at = datetime.utcnow()
    session.commit()
    return model_instance


def restore(session: Session, model_instance: T) -> T:
    """
    Restore a soft-deleted model instance by setting is_deleted=False and deleted_at=None.

    Args:
        session: SQLAlchemy session
        model_instance: The model instance to restore

    Returns:
        The updated model instance
    """
    model_instance.is_deleted = False
    model_instance.deleted_at = None
    session.commit()
    return model_instance


def get_active_query(session: Session, model_class: Type[T]):
    """
    Get a query that filters out soft-deleted records.

    Args:
        session: SQLAlchemy session
        model_class: The model class to query

    Returns:
        SQLAlchemy query with soft-deleted records filtered out
    """
    return session.query(model_class).filter(model_class.is_deleted == False)


def get_deleted_query(session: Session, model_class: Type[T]):
    """
    Get a query that returns only soft-deleted records.

    Args:
        session: SQLAlchemy session
        model_class: The model class to query

    Returns:
        SQLAlchemy query with only soft-deleted records
    """
    return session.query(model_class).filter(model_class.is_deleted == True)


def get_all_query(session: Session, model_class: Type[T]):
    """
    Get a query that returns all records (including soft-deleted).

    Args:
        session: SQLAlchemy session
        model_class: The model class to query

    Returns:
        SQLAlchemy query with all records
    """
    return session.query(model_class)


def soft_delete_user(session: Session, user_id: int) -> Optional[User]:
    """
    Soft delete a user and all their associated domains and aliases.

    Args:
        session: SQLAlchemy session
        user_id: ID of the user to soft delete

    Returns:
        The soft-deleted user instance or None if not found
    """
    user = session.get(User, user_id)
    if not user or user.is_deleted:
        return None

    # Soft delete all user's domains
    for domain in user.domains:
        if not domain.is_deleted:
            soft_delete(session, domain)

    # Soft delete all user's aliases
    for alias in user.aliases:
        if not alias.is_deleted:
            soft_delete(session, alias)

    # Soft delete the user
    return soft_delete(session, user)


def soft_delete_domain(session: Session, domain_id: int) -> Optional[Domain]:
    """
    Soft delete a domain and all its associated aliases.

    Args:
        session: SQLAlchemy session
        domain_id: ID of the domain to soft delete

    Returns:
        The soft-deleted domain instance or None if not found
    """
    domain = session.get(Domain, domain_id)
    if not domain or domain.is_deleted:
        return None

    # Soft delete all domain's aliases
    for alias in domain.aliases:
        if not alias.is_deleted:
            soft_delete(session, alias)

    # Soft delete the domain
    return soft_delete(session, domain)


def soft_delete_alias(session: Session, alias_id: int) -> Optional[Alias]:
    """
    Soft delete an alias.

    Args:
        session: SQLAlchemy session
        alias_id: ID of the alias to soft delete

    Returns:
        The soft-deleted alias instance or None if not found
    """
    alias = session.get(Alias, alias_id)
    if not alias or alias.is_deleted:
        return None

    return soft_delete(session, alias)


def is_soft_deleted(model_instance: T) -> bool:
    """
    Check if a model instance is soft deleted.

    Args:
        model_instance: The model instance to check

    Returns:
        True if the instance is soft deleted, False otherwise
    """
    return getattr(model_instance, "is_deleted", False)


def get_active_domains(session: Session, owner_id: Optional[int] = None):
    """
    Get all active (non-deleted) domains, optionally filtered by owner.

    Args:
        session: SQLAlchemy session
        owner_id: Optional owner ID to filter by

    Returns:
        Query for active domains
    """
    query = get_active_query(session, Domain)
    if owner_id:
        query = query.filter(Domain.owner_id == owner_id)
    return query


def get_active_aliases(
        session: Session, owner_id: Optional[int] = None, domain_id: Optional[int] = None
):
    """
    Get all active (non-deleted) aliases, optionally filtered by owner or domain.

    Args:
        session: SQLAlchemy session
        owner_id: Optional owner ID to filter by
        domain_id: Optional domain ID to filter by

    Returns:
        Query for active aliases
    """
    query = get_active_query(session, Alias)
    if owner_id:
        query = query.filter(Alias.owner_id == owner_id)
    if domain_id:
        query = query.filter(Alias.domain_id == domain_id)
    return query


def get_active_users(session: Session):
    """
    Get all active (non-deleted) users.

    Args:
        session: SQLAlchemy session

    Returns:
        Query for active users
    """
    return get_active_query(session, User)
