# UMT-pythonweb-hw-11

REST API для контактів на FastAPI з аутентифікацією, JWT-авторизацією, верифікацією email, обмеженням запитів до `/me`, CORS та оновленням аватара через Cloudinary.

## Можливості

- реєстрація користувача з перевіркою унікальності email;
- логін через `email` або `username` + `password` і видача `access_token`;
- хешування паролів через `passlib`;
- підтвердження email через токен верифікації;
- повторний запит листа для верифікації;
- доступ до контактів лише власника акаунта;
- CRUD для контактів, пошук і найближчі дні народження;
- маршрут `/api/users/me` з rate limiting;
- CORS middleware;
- оновлення аватара через Cloudinary;
- запуск через Docker Compose.

## Структура

```text
app/
  config.py
  database.py
  dependencies.py
  main.py
  models.py
  routes/
    auth.py
    contacts.py
    users.py
  services/
    auth.py
    cloudinary_service.py
    email.py
  schemas.py
tests/
  test_api.py
```

## Змінні середовища

Створи `.env` на базі `.env.example`.

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/contacts_db
JWT_SECRET_KEY=super-secret-jwt-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
EMAIL_VERIFICATION_SECRET=super-secret-email-key
APP_HOST=http://localhost:8000
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
RATE_LIMIT_ME_REQUESTS=5
RATE_LIMIT_WINDOW_SECONDS=60
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_SENDER=
SMTP_USE_TLS=true
```

## Запуск через Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

Після запуску:

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Основні маршрути

- `POST /api/auth/signup`
- `POST /api/auth/login`
- `GET /api/auth/verify-email/{token}`
- `POST /api/auth/request-email`
- `GET /api/users/me`
- `PATCH /api/users/avatar`
- `POST /api/contacts`
- `GET /api/contacts`
- `GET /api/contacts/{contact_id}`
- `PUT /api/contacts/{contact_id}`
- `DELETE /api/contacts/{contact_id}`
- `GET /api/contacts/upcoming/birthdays`

## Локальне тестування без Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Автотести

```bash
pytest -q
```

## Примітка про верифікацію email

Для реальної відправки листів заповни SMTP-змінні у `.env`. Якщо SMTP не налаштований, застосунок не падає, а логгує verification link у бекграунд-задачі.
