# Flask Notes Application - Backend

Production-ready Flask backend for the Notes application with JWT authentication, token revocation, and CRUD operations.

## Setup

### 1. Install Dependencies
\`\`\`bash
pipenv install
\`\`\`

### 2. Configure Environment
\`\`\`bash
cp .env.example .env
\`\`\`

### 3. Seed Database
\`\`\`bash
pipenv run python seed.py
\`\`\`

### 4. Run Server
\`\`\`bash
pipenv run python run.py
\`\`\`

Server runs on http://localhost:5000

### 5. Run Tests
\`\`\`bash
pipenv run pytest
\`\`\`

## API Endpoints

- POST /api/auth/signup
- POST /api/auth/login
- POST /api/auth/logout
- GET /api/auth/me
- GET /api/notes
- POST /api/notes
- GET /api/notes/<id>
- PATCH /api/notes/<id>
- DELETE /api/notes/<id>

## Demo Credentials

- alice / password123
- bob / password123