"""
File Storage Service Module.
Handles all business logic for file upload, deletion, and management (avatars, documents, etc.).
Following architectural rules: stateless, encapsulates file system operations.
"""
import os
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import HTTPException, status, UploadFile

from app.models.user import User


class FileStorageService:
    """Service for managing file storage operations."""

    # Configuration
    AVATARS_DIR = Path("public/avatars")
    MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/jpg", "image/webp"]

    @staticmethod
    def upload_avatar(file: UploadFile, user: User, contents: bytes) -> Dict[str, Any]:
        """
        Upload user avatar image.
        Returns avatar URL and success message.
        """
        # Validate file type
        if file.content_type not in FileStorageService.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only JPEG, PNG, and WebP images are allowed.",
            )

        # Validate file size
        if len(contents) > FileStorageService.MAX_AVATAR_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size too large. Maximum size is 5MB.",
            )

        # Create avatars directory if it doesn't exist
        FileStorageService.AVATARS_DIR.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = FileStorageService.AVATARS_DIR / unique_filename

        # Save file
        with open(file_path, "wb") as f:
            f.write(contents)

        # Delete old avatar if it exists and is not a Google avatar
        if user.avatar_url and not user.avatar_url.startswith("http"):
            FileStorageService._delete_file_safely(Path(user.avatar_url))

        # Return avatar URL
        avatar_url = f"public/avatars/{unique_filename}"

        return {"message": "Avatar uploaded successfully", "avatar_url": avatar_url}

    @staticmethod
    def delete_avatar(user: User) -> Dict[str, str]:
        """
        Delete user avatar.
        Returns success message.
        """
        if not user.avatar_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No avatar to delete"
            )

        # Don't delete Google avatars
        if user.avatar_url.startswith("http"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete Google avatar",
            )

        # Delete file from disk
        file_path = Path(user.avatar_url)
        if file_path.exists():
            try:
                os.remove(file_path)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete avatar file: {str(e)}",
                )

        return {"message": "Avatar deleted successfully"}

    @staticmethod
    def _delete_file_safely(file_path: Path):
        """Delete a file safely, ignoring errors."""
        if file_path.exists():
            try:
                os.remove(file_path)
            except Exception:
                pass  # Ignore errors when deleting old file

    @staticmethod
    def get_avatar_url(user: User) -> Optional[str]:
        """Get avatar URL for a user."""
        return user.avatar_url
