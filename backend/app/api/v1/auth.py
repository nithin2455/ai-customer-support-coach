from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.core.security import hash_password, verify_password, create_access_token
from app.models.domain import User, Customer, Agent
from app.schemas.auth import RegisterRequest, LoginRequest, UserOut, TokenResponse

router = APIRouter()


def _format_user_out(user: User) -> UserOut:
    customer_id = user.customer_profile.id if user.customer_profile else None
    agent_id = user.agent_profile.id if user.agent_profile else None
    tier = user.customer_profile.tier if user.customer_profile else None
    dept_name = None
    if user.agent_profile and user.agent_profile.department:
        dept_name = user.agent_profile.department.name

    return UserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        customer_id=customer_id,
        agent_id=agent_id,
        tier=tier,
        department_name=dept_name,
        created_at=user.created_at
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_customer(req: RegisterRequest, db: Session = Depends(get_db)):
    """
    Registers a new customer account.
    Validates input, hashes password, creates User and Customer records,
    and returns a signed JWT access token.
    """
    if req.confirm_password is not None and req.password != req.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match."
        )

    clean_email = str(req.email).lower().strip()

    # Check for existing email
    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # 1. Create User
    new_user = User(
        name=req.name.strip(),
        email=clean_email,
        role="customer",
        hashed_password=hash_password(req.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 2. Create Customer Profile
    new_customer = Customer(
        user_id=new_user.id,
        tier="Standard",
        total_contacts=0,
        unresolved_issues=0,
        current_stress_score=0,
        predicted_style="Calm"
    )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    db.refresh(new_user)

    # 3. Create Access Token
    token = create_access_token({
        "sub": str(new_user.id),
        "email": new_user.email,
        "role": new_user.role,
        "customer_id": new_customer.id
    })

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=_format_user_out(new_user)
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates user with email and password.
    Returns signed JWT access token and user identity.
    """
    clean_email = str(req.email).lower().strip()
    user = db.query(User).filter(User.email == clean_email).first()

    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    extra_claims = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role
    }
    if user.customer_profile:
        extra_claims["customer_id"] = user.customer_profile.id
    if user.agent_profile:
        extra_claims["agent_id"] = user.agent_profile.id

    token = create_access_token(extra_claims)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=_format_user_out(user)
    )


@router.get("/me", response_model=UserOut)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Returns the authenticated user's profile and linked customer/agent info.
    """
    return _format_user_out(current_user)


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """
    Acknowledges user logout.
    Client-side invalidation removes the stored JWT token.
    """
    return {"message": f"Successfully logged out {current_user.name}."}
