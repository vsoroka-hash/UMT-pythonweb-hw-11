from fastapi import HTTPException, UploadFile, status

from app.config import settings


def upload_avatar(file: UploadFile, user_id: int) -> str:
    if not all(
        [
            settings.cloudinary_cloud_name,
            settings.cloudinary_api_key,
            settings.cloudinary_api_secret,
        ]
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cloudinary is not configured.",
        )

    import cloudinary
    import cloudinary.uploader

    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )

    result = cloudinary.uploader.upload(
        file.file,
        public_id=f"user_{user_id}",
        folder="contacts_api_avatars",
        overwrite=True,
    )
    return result["secure_url"]
