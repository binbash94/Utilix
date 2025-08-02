from fastapi import APIRouter, Depends
from ...deps import get_current_user
from ....schemas.user import UserRead
from ....models.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: User = Depends(get_current_user)):
    """
    Return the profile of the authenticated user.
    """
    return current_user
