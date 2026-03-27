from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(..., alias="DATABASE_URL")
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(..., alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(..., alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    email_verification_secret: str = Field(..., alias="EMAIL_VERIFICATION_SECRET")
    app_host: str = Field(..., alias="APP_HOST")
    cors_origins: str = Field(..., alias="CORS_ORIGINS")
    rate_limit_me_requests: int = Field(..., alias="RATE_LIMIT_ME_REQUESTS")
    rate_limit_window_seconds: int = Field(..., alias="RATE_LIMIT_WINDOW_SECONDS")
    cloudinary_cloud_name: str = Field(default="", alias="CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key: str = Field(default="", alias="CLOUDINARY_API_KEY")
    cloudinary_api_secret: str = Field(default="", alias="CLOUDINARY_API_SECRET")
    smtp_host: str = Field(default="", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str = Field(default="", alias="SMTP_USER")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    smtp_sender: str = Field(default="", alias="SMTP_SENDER")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def get_cors_origins(self):
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


settings = Settings()
