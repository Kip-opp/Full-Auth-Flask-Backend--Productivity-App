# Full-Stack Notes Application

A complete, production-ready notes application built with Flask (backend) and vanilla JavaScript (frontend). Features JWT authentication, token revocation, and full CRUD operations for notes management.

**Original Repository**: [https://github.com/Kip-opp/Full-Auth-Flask-Backend--Productivity-App.git](https://github.com/Kip-opp/Full-Auth-Flask-Backend--Productivity-App.git)

## 🚀 Features

### Backend (Flask)
- JWT-based authentication with token revocation
- User registration and login
- Full CRUD operations for notes
- Database migrations with Alembic
- Comprehensive test suite
- Production-ready configuration

### Frontend (Vanilla JavaScript)
- User authentication (login/signup)
- Create, read, update, delete notes
- Filter notes by status (active/archived)
- Pagination support
- Responsive design
- Real-time updates
- Clean, intuitive UI
- Logout confirmation dialog

## 🛠 Tech Stack

### Backend
- **Python 3.8+**
- **Flask** - Web framework
- **Flask-SQLAlchemy** - ORM
- **Flask-Migrate** - Database migrations
- **Flask-Bcrypt** - Password hashing
- **PyJWT** - JWT authentication
- **Flask-CORS** - Cross-origin resource sharing
- **Pipenv** - Dependency management
- **SQLite** - Database (development)
- **PostgreSQL** - Database (production)

### Frontend
- **HTML5** - Structure
- **CSS3** - Styling with Flexbox/Grid
- **Vanilla JavaScript (ES6+)** - No frameworks
- **Fetch API** - HTTP requests
- **Local Storage** - Token persistence

## 📦 Project Structure

```
notes-app/
├── backend/                    # Flask backend application
│   ├── app/
│   │   ├── __init__.py        # Application factory
│   │   ├── config.py          # Configuration settings
│   │   ├── extensions.py      # Flask extensions
│   │   ├── models/            # Database models
│   │   │   ├── __init__.py
│   │   │   ├── user.py        # User model
│   │   │   └── note.py        # Note model
│   │   ├── routes/            # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── auth.py        # Authentication routes
│   │   │   └── notes.py       # Notes routes
│   │   ├── schemas/           # Data validation schemas
│   │   │   ├── __init__.py
│   │   │   ├── user_schema.py
│   │   │   └── note_schema.py
│   │   └── utils/             # Utility functions
│   │       ├── __init__.py
│   │       ├── responses.py   # Response helpers
│   │       └── decorators.py  # Custom decorators
│   ├── migrations/            # Database migrations
│   ├── tests/                 # Test suite
│   ├── run.py                 # Application entry point
│   ├── seed.py                # Database seeding
│   ├── Pipfile               # Dependencies
│   └── README.md             # Backend documentation
├── frontend/                   # Static frontend files
│   ├── index.html            # Main HTML file
│   ├── css/
│   │   ├── style.css         # Main styles
│   │   └── responsive.css    # Responsive styles
│   └── js/                   # JavaScript modules
│       ├── api.js           # API service
│       ├── auth.js          # Authentication module
│       ├── notes.js         # Notes module
│       └── main.js          # Application entry point
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Pipenv (`pip install pipenv`)

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/Kip-opp/Full-Auth-Flask-Backend--Productivity-App.git
cd Full-Auth-Flask-Backend--Productivity-App

# Navigate to backend directory
cd backend

# Install dependencies
pipenv install

# Configure environment (optional)
cp .env.example .env

# Seed database with demo users
pipenv run python seed.py

# Initialize database migrations
pipenv run flask db upgrade

# Start development server
pipenv run python run.py
```

The backend will be available at `http://localhost:5000`

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Option 1: Open index.html directly in browser
# Option 2: Serve with a local server
python -m http.server 8000
```

The frontend will be available at `http://localhost:8000`

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Backend (.env)
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key
JWT_EXPIRATION_HOURS=168
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,http://localhost:5500
```

## 📚 API Documentation

### Authentication Endpoints

#### POST /api/auth/signup
Register a new user
```json
{
  "username": "testuser",
  "email": "user@example.com",
  "password": "password123"
}
```

#### POST /api/auth/login
Authenticate user and get token
```json
{
  "username": "testuser",
  "password": "password123"
}
```

#### POST /api/auth/logout
Logout user (requires valid JWT in Authorization header)

#### GET /api/auth/me
Get current user info (requires valid JWT)

### Notes Endpoints

#### GET /api/notes
Get all notes for current user
- Query params: `page`, `per_page`, `status`

#### POST /api/notes
Create a new note
```json
{
  "title": "My Note",
  "content": "Note content here",
  "status": "active"
}
```

#### GET /api/notes/<id>
Get specific note by ID

#### PATCH /api/notes/<id>
Update a note
```json
{
  "title": "Updated Title",
  "content": "Updated content",
  "status": "archived"
}
```

#### DELETE /api/notes/<id>
Delete a note

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  username VARCHAR(80) UNIQUE NOT NULL,
  email VARCHAR(120) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Notes Table
```sql
CREATE TABLE notes (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  title VARCHAR(255) NOT NULL,
  content TEXT NOT NULL,
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### Token Blocklist Table
```sql
CREATE TABLE token_blocklist (
  id INTEGER PRIMARY KEY,
  token TEXT NOT NULL,
  user_id INTEGER NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pipenv run pytest
```

### Frontend Testing
Manual testing through the browser interface.

## 🎯 Demo

### Demo Credentials
- **Username**: alice
- **Password**: password123

- **Username**: bob  
- **Password**: password123

## 🔒 Security Features

- JWT authentication with secure token storage
- Token revocation on logout
- Password hashing with bcrypt
- CORS protection
- Input validation and sanitization
- Field-specific error messages
- Form validation with required field toggling

## 🚀 Deployment

### Backend Deployment
1. Set production environment variables
2. Use a production WSGI server (Gunicorn, uWSGI)
3. Configure reverse proxy (Nginx)
4. Set up production database (PostgreSQL)

### Frontend Deployment
1. Serve static files through CDN or web server
2. Update `API_URL` in `frontend/js/api.js` to your production backend

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Flask ecosystem for robust backend development
- Modern JavaScript for clean frontend implementation
- Alembic for database migrations
- JWT for secure authentication
