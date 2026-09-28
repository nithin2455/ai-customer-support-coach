from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.models.domain import User, Customer, Agent

# Optional bearer token scheme (won't fail automatically so we can provide custom 401/403 errors and optional fallback)
bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator:
    """Provides a database session to API route handlers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_optional_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Returns the authenticated User if valid Bearer token is provided,
    or None if no Authorization header is present.
    """
    if not auth or not auth.credentials:
        return None
    payload = decode_access_token(auth.credentials)
    if not payload or "sub" not in payload:
        return None
    user_id = payload.get("sub")
    try:
        user = db.query(User).filter(User.id == int(user_id)).first()
        return user
    except (ValueError, TypeError):
        return None


def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Validates JWT Bearer token and returns authenticated User entity.
    Raises 401 Unauthorized if missing, expired, or invalid.
    """
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(auth.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id = int(payload.get("sub"))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_customer(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Customer:
    """
    Ensures authenticated user is a Customer and returns their Customer profile.
    Raises 403 Forbidden if user role is not 'customer'.
    """
    if current_user.role != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Customer access only."
        )
    customer = current_user.customer_profile
    if not customer:
        # If customer profile doesn't exist, auto-create one for consistency
        customer = Customer(
            user_id=current_user.id,
            tier="Standard",
            total_contacts=0,
            unresolved_issues=0,
            current_stress_score=0,
            predicted_style="Calm"
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
    return customer


def get_current_agent(
    current_user: User = Depends(get_current_user)
) -> Agent:
    """
    Ensures authenticated user is an Agent or Admin.
    Raises 403 Forbidden if user is a customer.
    """
    if current_user.role not in ["agent", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Agent or Admin access required."
        )
    if current_user.agent_profile:
        return current_user.agent_profile
    # For admin without specific agent record, return mock agent structure or allow access
    return current_user


def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Ensures authenticated user is an Admin.
    Raises 403 Forbidden if user role is not 'admin'.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Administrator access required."
        )
    return current_user
