# backend/app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from ...deps import get_session, get_current_user
from ....schemas.token import Token
from ....schemas.user import UserCreate, UserRead
from ....crud.crud_user import crud_user
from ....core.security import create_access_token
from ....models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


# ───────────────────────────────────────────────────────────────
#  Register
# ───────────────────────────────────────────────────────────────
@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_session),
):
    existing = await crud_user.get_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    user = await crud_user.create(db, obj_in=payload)
    return user


# ───────────────────────────────────────────────────────────────
#  Login → JWT token
# ───────────────────────────────────────────────────────────────
@router.post("/token", response_model=Token)
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session),
):
    user = await crud_user.authenticate(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = create_access_token(str(user.id))
    return {"access_token": access_token, "token_type": "bearer"}


# ───────────────────────────────────────────────────────────────
#  Current user convenience
# ───────────────────────────────────────────────────────────────
@router.get("/me", response_model=UserRead)
async def read_me(current_user: User = Depends(get_current_user)):
    return current_user
