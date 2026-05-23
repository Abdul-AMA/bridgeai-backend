from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.user import User, UserRole


def verify_super_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )
    return current_user
