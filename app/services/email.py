import logging
import smtplib
from email.message import EmailMessage

from fastapi import BackgroundTasks
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import settings


logger = logging.getLogger(__name__)


def get_email_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.email_verification_secret)


def create_email_verification_token(email: str) -> str:
    serializer = get_email_serializer()
    return serializer.dumps(email, salt="email-verification")


def verify_email_token(token: str, max_age: int = 3600) -> str:
    serializer = get_email_serializer()
    try:
        return serializer.loads(token, salt="email-verification", max_age=max_age)
    except (BadSignature, SignatureExpired):
        raise ValueError("Invalid or expired email verification token.")


def send_verification_email(background_tasks: BackgroundTasks, email: str) -> str:
    token = create_email_verification_token(email)
    verification_link = f"{settings.app_host}/api/auth/verify-email/{token}"
    background_tasks.add_task(deliver_verification_email, email, verification_link)
    return verification_link


def deliver_verification_email(email: str, verification_link: str) -> None:
    if not all(
        [
            settings.smtp_host,
            settings.smtp_user,
            settings.smtp_password,
            settings.smtp_sender,
        ]
    ):
        logger.warning("SMTP is not configured. Verification link for %s: %s", email, verification_link)
        return

    message = EmailMessage()
    message["Subject"] = "Verify your email"
    message["From"] = settings.smtp_sender
    message["To"] = email
    message.set_content(
        "Welcome to Contacts API.\n\n"
        f"Please verify your email by visiting this link:\n{verification_link}\n"
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        if settings.smtp_use_tls:
            server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(message)
