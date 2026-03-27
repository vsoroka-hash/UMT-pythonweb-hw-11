import os
import sys
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient


TEST_DB_PATH = Path("test_api_hw11.db")
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["EMAIL_VERIFICATION_SECRET"] = "test-email-secret"
os.environ["CLOUDINARY_CLOUD_NAME"] = "test"
os.environ["CLOUDINARY_API_KEY"] = "test"
os.environ["CLOUDINARY_API_SECRET"] = "test"
os.environ["RATE_LIMIT_ME_REQUESTS"] = "2"
os.environ["RATE_LIMIT_WINDOW_SECONDS"] = "60"
os.environ["APP_HOST"] = "http://testserver"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://127.0.0.1:3000"

from app.database import Base, engine  # noqa: E402
from app.dependencies import me_request_history  # noqa: E402
from app.main import app  # noqa: E402
from app.services.email import create_email_verification_token  # noqa: E402


def setup_module():
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    Base.metadata.create_all(bind=engine)


def teardown_module():
    Base.metadata.drop_all(bind=engine)
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


def get_client() -> TestClient:
    return TestClient(app)


def upcoming_birthday(days_from_today: int = 2) -> str:
    return (date.today() + timedelta(days=days_from_today)).isoformat()


def distant_birthday(days_from_today: int = 20) -> str:
    return (date.today() + timedelta(days=days_from_today)).isoformat()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_signup_login_verify_and_duplicate_signup():
    with get_client() as client:
        signup_response = client.post(
            "/api/auth/signup",
            json={
                "username": "volodymyr",
                "email": "volodymyr@example.com",
                "password": "secret123",
            },
        )
        assert signup_response.status_code == 201
        assert signup_response.json()["email"] == "volodymyr@example.com"
        assert signup_response.json()["verified_email"] is False

        duplicate_response = client.post(
            "/api/auth/signup",
            json={
                "username": "another",
                "email": "volodymyr@example.com",
                "password": "secret123",
            },
        )
        assert duplicate_response.status_code == 409

        bad_login = client.post(
            "/api/auth/login",
            json={"email": "volodymyr@example.com", "password": "wrongpass"},
        )
        assert bad_login.status_code == 401

        login_response = client.post(
            "/api/auth/login",
            json={"email": "volodymyr@example.com", "password": "secret123"},
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        assert access_token

        username_login_response = client.post(
            "/api/auth/login",
            json={"username": "volodymyr", "password": "secret123"},
        )
        assert username_login_response.status_code == 200

        verify_token = create_email_verification_token("volodymyr@example.com")
        verify_response = client.get(f"/api/auth/verify-email/{verify_token}")
        assert verify_response.status_code == 200
        assert verify_response.json()["message"] == "Email successfully verified."

        headers = auth_headers(access_token)
        me_response = client.get("/api/users/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["verified_email"] is True


def test_user_specific_contacts_and_protected_routes():
    with get_client() as client:
        client.post(
            "/api/auth/signup",
            json={
                "username": "anna",
                "email": "anna@example.com",
                "password": "secret123",
            },
        )

        token_user_1 = client.post(
            "/api/auth/login",
            json={"email": "volodymyr@example.com", "password": "secret123"},
        ).json()["access_token"]
        token_user_2 = client.post(
            "/api/auth/login",
            json={"email": "anna@example.com", "password": "secret123"},
        ).json()["access_token"]

        unauthorized_response = client.get("/api/contacts")
        assert unauthorized_response.status_code == 401

        create_response = client.post(
            "/api/contacts",
            json={
                "first_name": "Ivan",
                "last_name": "Petrenko",
                "email": "ivan@example.com",
                "phone_number": "+380501234567",
                "birthday": upcoming_birthday(),
                "additional_data": "friend",
            },
            headers=auth_headers(token_user_1),
        )
        assert create_response.status_code == 201
        contact_id = create_response.json()["id"]

        list_user_1 = client.get("/api/contacts", headers=auth_headers(token_user_1))
        assert list_user_1.status_code == 200
        assert len(list_user_1.json()) == 1

        search_response = client.get(
            "/api/contacts",
            params={"first_name": "Ivan"},
            headers=auth_headers(token_user_1),
        )
        assert len(search_response.json()) == 1

        birthdays = client.get(
            "/api/contacts/upcoming/birthdays",
            headers=auth_headers(token_user_1),
        )
        assert birthdays.status_code == 200
        assert len(birthdays.json()) == 1

        user_2_access = client.get(
            f"/api/contacts/{contact_id}",
            headers=auth_headers(token_user_2),
        )
        assert user_2_access.status_code == 404

        update_response = client.put(
            f"/api/contacts/{contact_id}",
            json={
                "first_name": "Ivan",
                "last_name": "Updated",
                "email": "ivan.updated@example.com",
                "phone_number": "+380501234567",
                "birthday": distant_birthday(),
                "additional_data": "updated",
            },
            headers=auth_headers(token_user_1),
        )
        assert update_response.status_code == 200
        assert update_response.json()["last_name"] == "Updated"

        delete_response = client.delete(
            f"/api/contacts/{contact_id}",
            headers=auth_headers(token_user_1),
        )
        assert delete_response.status_code == 200


def test_request_email_rate_limit_and_avatar_upload(monkeypatch):
    with get_client() as client:
        login_response = client.post(
            "/api/auth/login",
            json={"email": "volodymyr@example.com", "password": "secret123"},
        )
        token = login_response.json()["access_token"]
        headers = auth_headers(token)

        email_request = client.post(
            "/api/auth/request-email",
            json={"email": "volodymyr@example.com"},
        )
        assert email_request.status_code == 200

        me_request_history.clear()
        first_me = client.get("/api/users/me", headers=headers)
        second_me = client.get("/api/users/me", headers=headers)
        third_me = client.get("/api/users/me", headers=headers)
        assert first_me.status_code == 200
        assert second_me.status_code == 200
        assert third_me.status_code == 429

        def fake_upload_avatar(file, user_id):
            assert user_id > 0
            return "https://res.cloudinary.com/demo/image/upload/avatar.jpg"

        monkeypatch.setattr("app.routes.users.upload_avatar", fake_upload_avatar)

        avatar_response = client.patch(
            "/api/users/avatar",
            headers=headers,
            files={"file": ("avatar.jpg", BytesIO(b"avatar-bytes"), "image/jpeg")},
        )
        assert avatar_response.status_code == 201
        assert avatar_response.json()["avatar_url"].startswith("https://res.cloudinary.com")
