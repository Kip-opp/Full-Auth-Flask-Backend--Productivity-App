# AI Todo Backend

## Project Description
AI Todo Backend is a secure Flask API for managing personal todos.  
It uses JWT authentication so users can sign up, log in, and manage only their own tasks.  
Each todo belongs to a user and supports full CRUD actions, notes, priority, due dates, and pagination on the index route.

## Features
- User signup and login with JWT authentication
- Secure password hashing with Flask-Bcrypt
- Protected `me` endpoint for current user
- User-owned todo resource
- Full CRUD for todos
- Pagination on the todo index route
- Ownership protection so users only access their own records
- Seed file for demo data
- Optional CLI for terminal interaction

## Tech Stack
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-JWT-Extended
- Flask-Bcrypt
- SQLite
- Python

## Project Structure
```bash
ai_todo_backend/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── todo.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── todos.py
│   ├── services/
│   │   └── ai_service.py
│   └── utils/
│       └── decorators.py
├── migrations/
├── cli.py
├── run.py
├── seed.py
├── requirements.txt
├── README.md
└── .env
```

## Installation Instructions

### 1. Clone the repository
```bash
git clone git@github.com:Kip-opp/Full-Auth-Flask-Backend--Productivity-App.git
cd Full-Auth-Flask-Backend--Productivity-App
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create environment variables
Create a `.env` file in the project root:

```env
SECRET_KEY=super-secret-key
JWT_SECRET_KEY=jwt-super-secret-key
DATABASE_URL=sqlite:///todo.db

AI_PROVIDER=grok
XAI_API_KEY=your_xai_api_key_here
XAI_BASE_URL=https://api.x.ai/v1
XAI_MODEL=grok-4-1-fast-non-reasoning
```

## Database Migration Instructions
```bash
export FLASK_APP=run.py
flask db init
flask db migrate -m "initial migration"
flask db upgrade
```

If migrations already exist, only run:

```bash
export FLASK_APP=run.py
flask db upgrade
```

## Seed the Database
```bash
python seed.py
```

## Run Instructions

### Start the Flask server
```bash
python run.py
```

The API will run at:

```bash
http://127.0.0.1:5000
```

### Optional: Run the CLI
```bash
python cli.py
```

## Authentication
This API uses JWT authentication.  
After login, copy the returned `access_token` and send it in protected requests using:

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

## API Endpoints

### Auth Endpoints

#### `POST /api/auth/signup`
Create a new user.

Request body:
```json
{
  "username": "kyp",
  "email": "kyp@example.com",
  "password": "12345678"
}
```

#### `POST /api/auth/login`
Authenticate a user and return a JWT token.

Request body:
```json
{
  "email": "kyp@example.com",
  "password": "12345678"
}
```

#### `GET /api/auth/me`
Return the currently authenticated user.  
Requires Bearer token.

---

### Todo Endpoints

#### `GET /api/todos?page=1&per_page=5`
Return paginated todos for the authenticated user only.  
Optional query params:
- `page`
- `per_page`
- `status=pending|completed`
- `scope=upcoming|previous`

#### `POST /api/todos`
Create a new todo for the authenticated user.

Request body:
```json
{
  "title": "Finish Flask project",
  "description": "Complete the backend routes",
  "notes": "Remember pagination and me endpoint",
  "priority": "high",
  "due_date": "2026-04-20T09:00:00"
}
```

#### `GET /api/todos/<id>`
Return one todo owned by the authenticated user.

#### `PATCH /api/todos/<id>`
Update fields on a todo owned by the authenticated user.

Example request body:
```json
{
  "completed": true,
  "notes": "Finished and tested in Postman"
}
```

#### `DELETE /api/todos/<id>`
Delete a todo owned by the authenticated user.

## Demo Accounts
After running `python seed.py`, you can log in with:

```txt
demo@example.com / password123
alice@example.com / alice123
```

## Testing With Postman
1. Sign up or log in
2. Copy the `access_token`
3. Use Bearer Token auth in Postman
4. Test the protected `/api/auth/me` and `/api/todos` routes

## Future Improvements
- Refresh tokens
- Logout token blocklist
- Automated tests with pytest
- HTML or React frontend
- Better AI planning prompts