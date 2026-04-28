# Full-Stack Notes Application

## Project Overview

This is a comprehensive full-stack productivity notes application that allows users to create, manage, and organize their personal notes securely. The application features a robust backend built with Flask and SQLAlchemy, providing RESTful APIs for authentication and note management. The frontend is a responsive single-page application built with vanilla JavaScript, offering an intuitive user interface for note creation, editing, and organization.

The application implements JWT-based authentication to ensure secure user sessions and data privacy. Each user can create multiple notes with titles, content, and status management (active/archived). The system includes pagination for efficient data retrieval and filtering capabilities to help users organize their notes effectively.

## Key Features

### Backend Features
- **JWT Authentication**: Secure token-based authentication with automatic token refresh and logout functionality
- **User Management**: Complete user registration, login, and profile management with password hashing
- **Notes CRUD Operations**: Full create, read, update, and delete functionality for notes with ownership validation
- **Status Management**: Notes can be marked as active or archived for better organization
- **Pagination**: Configurable pagination to handle large datasets efficiently (10 items per page, max 100)
- **Input Validation**: Comprehensive validation using Marshmallow schemas with detailed error messages
- **Database Migrations**: Support for database schema evolution using Flask-Migrate
- **CORS Configuration**: Cross-origin resource sharing setup for seamless frontend integration

### Frontend Features
- **Responsive Design**: Mobile-first design that adapts to different screen sizes
- **Single-Page Application**: Fast, dynamic user interface without page reloads
- **Modal-Based Interactions**: Clean modal dialogs for note creation and editing
- **Real-Time Feedback**: Success and error notifications for user actions
- **Pagination Controls**: User-friendly pagination for browsing through notes
- **Status Filtering**: Filter notes by active/archived status
- **Form Validation**: Client-side validation with clear error messages
- **Persistent Sessions**: Automatic token management and session persistence

## Tech Stack

### Backend
- **Python 3.8+**
- **Flask 2.2.2**: Lightweight WSGI web application framework
- **SQLAlchemy**: Python SQL toolkit and Object-Relational Mapping (ORM)
- **Flask-Migrate**: Database migration management
- **Flask-CORS**: Cross-origin resource sharing support
- **PyJWT**: JSON Web Token implementation
- **bcrypt**: Password hashing library
- **Marshmallow**: Object serialization/deserialization and validation
- **pytest**: Testing framework with comprehensive test coverage

### Frontend
- **Vanilla JavaScript (ES6+)**: Modern JavaScript with modules for clean architecture
- **HTML5**: Semantic markup for accessibility
- **CSS3**: Custom properties (CSS variables) for theming and responsive design
- **Fetch API**: Modern browser API for HTTP requests

### Database
- **SQLite**: Default development database (easily configurable for PostgreSQL/MySQL in production)

### Development Tools
- **Pipenv**: Python dependency management
- **Alembic**: Database migration tool
- **Git**: Version control
- **Postman**: API testing and documentation

## Project Structure

```
Full-Auth-Flask-Backend--Productivity-App/
├── backend/                    # Flask backend application
│   ├── app/
│   │   ├── __init__.py         # Flask application factory - creates and configures the app instance
│   │   ├── config.py           # Configuration classes for different environments (dev/test/prod)
│   │   ├── extensions.py       # Flask extensions initialization (SQLAlchemy, Migrate, CORS)
│   │   ├── models/
│   │   │   ├── __init__.py     # Model imports and relationships
│   │   │   ├── user.py         # User model with authentication methods
│   │   │   └── note.py         # Note model and TokenBlocklist for logout functionality
│   │   ├── routes/
│   │   │   ├── __init__.py     # Blueprint registrations
│   │   │   ├── auth.py         # Authentication routes (signup/login/logout/me)
│   │   │   └── notes.py        # Notes CRUD routes with ownership validation
│   │   ├── schemas/
│   │   │   ├── __init__.py     # Schema imports
│   │   │   ├── user_schema.py  # User data validation schemas
│   │   │   └── note_schema.py  # Note data validation schemas
│   │   └── utils/
│   │       ├── __init__.py     # Utility imports
│   │       ├── decorators.py   # token_required decorator for route protection
│   │       └── responses.py    # Standardized API response helpers
│   ├── instance/               # SQLite database storage (not in version control)
│   ├── migrations/             # Database migration scripts
│   ├── tests/
│   │   ├── __init__.py         # Test configuration
│   │   ├── test_auth.py        # Authentication endpoint tests
│   │   └── test_notes.py       # Notes CRUD operation tests
│   ├── Pipfile                 # Python dependencies specification
│   ├── Pipfile.lock            # Locked dependency versions
│   ├── pytest.ini             # Pytest configuration
│   ├── run.py                 # Application entry point
│   ├── seed.py                # Database seeding script for development
│   └── README.md              # Backend-specific setup instructions
├── client-with-jwt/           # Vanilla JavaScript frontend
│   ├── css/
│   │   ├── style.css          # Main application styles with CSS variables
│   │   └── responsive.css     # Responsive design rules for mobile/tablet
│   ├── js/
│   │   ├── api.js             # Centralized API service class for HTTP requests
│   │   ├── auth.js            # Authentication module handling login/signup/logout
│   │   ├── main.js            # Application initialization and routing
│   │   └── notes.js           # Notes management module with CRUD operations
│   ├── index.html             # Single-page application HTML template
│   ├── .env.example           # Environment variables template
│   └── .gitignore             # Frontend-specific ignore rules
├── .gitignore                 # Root-level ignore rules
└── README.md                  # This file - main project documentation
```

## Prerequisites

Before setting up the application, ensure you have the following installed:

- **Python 3.8 or higher**
- **Node.js** (for any frontend tooling, though not required for vanilla JS)
- **Git** for version control
- **Postman** or similar tool for API testing (optional but recommended)

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Full-Auth-Flask-Backend--Productivity-App
   ```

2. **Set up the backend:**
   ```bash
   cd backend
   pipenv install
   pipenv shell
   ```

3. **Set up the frontend:**
   The frontend uses vanilla JavaScript and requires no build process. Simply ensure a modern web browser is available.

## Setup and Run Instructions

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Activate virtual environment:**
   ```bash
   pipenv shell
   ```

3. **Environment configuration:**
   Copy the environment template and configure your settings:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your configuration:
   ```
   SECRET_KEY=your-secret-key-here
   JWT_SECRET_KEY=your-jwt-secret-key-here
   FLASK_ENV=development
   CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   ```

4. **Database setup:**
   ```bash
   flask db init    # Only if migrations folder doesn't exist
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

5. **Seed the database (optional for development):**
   ```bash
   python seed.py
   ```

6. **Run the backend server:**
   ```bash
   python run.py
   ```
   The server will start on `http://localhost:5000`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd client-with-jwt
   ```

2. **Configure API endpoint (if needed):**
   The frontend automatically detects the API URL. For custom configurations, edit the `js/api.js` file.

3. **Start the frontend:**
   Simply open `index.html` in a modern web browser, or use a local server:
   ```bash
   # Using Python's built-in server
   python -m http.server 3000

   # Or using Node.js
   npx http-server -p 3000
   ```
   Access the application at `http://localhost:3000`

## Database Setup and SQL Schema Details

### Database Configuration
The application uses SQLite by default for development. To use PostgreSQL or MySQL in production, update the `SQLALCHEMY_DATABASE_URI` in your configuration.

### Schema Overview

#### Users Table
```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```
- Stores user account information with unique constraints on username and email
- Passwords are hashed using bcrypt before storage
- Timestamps track creation and last update

#### Notes Table
```sql
CREATE TABLE note (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    status VARCHAR(20) DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);
```
- Each note belongs to a user (foreign key relationship)
- Status can be 'active' or 'archived'
- Cascade delete ensures notes are removed when user is deleted

#### Token Blocklist Table
```sql
CREATE TABLE token_blocklist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token VARCHAR(500) NOT NULL,
    user_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE SET NULL
);
```
- Stores invalidated JWT tokens for logout functionality
- Tokens expire automatically after the configured time (168 hours default)

### Database Relationships
- **One-to-Many**: User → Notes (one user can have multiple notes)
- **One-to-Many**: User → TokenBlocklist (one user can have multiple blocked tokens)
- **Cascade Operations**: Deleting a user removes all associated notes and sets token blocklist user_id to NULL

## API Documentation

The API follows RESTful conventions with JSON request/response formats. All protected endpoints require JWT authentication via the `Authorization: Bearer <token>` header.

### Authentication Endpoints (`/api/auth`)

#### User Registration
- **Method**: `POST`
- **Endpoint**: `/api/auth/signup`
- **Description**: Register a new user account
- **Request Body**:
  ```json
  {
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securepassword123"
  }
  ```
- **Response** (201 Created):
  ```json
  {
    "message": "User created successfully",
    "user": {
      "id": 1,
      "username": "johndoe",
      "email": "john@example.com"
    },
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
  ```

#### User Login
- **Method**: `POST`
- **Endpoint**: `/api/auth/login`
- **Description**: Authenticate user and receive JWT token
- **Request Body**:
  ```json
  {
    "email": "john@example.com",
    "password": "securepassword123"
  }
  ```
- **Response** (200 OK):
  ```json
  {
    "message": "Login successful",
    "user": {
      "id": 1,
      "username": "johndoe",
      "email": "john@example.com"
    },
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
  ```

#### User Logout
- **Method**: `POST`
- **Endpoint**: `/api/auth/logout`
- **Description**: Invalidate the current JWT token
- **Headers**: `Authorization: Bearer <token>`
- **Response** (200 OK):
  ```json
  {
    "message": "Logout successful"
  }
  ```

#### Get Current User
- **Method**: `GET`
- **Endpoint**: `/api/auth/me`
- **Description**: Retrieve current authenticated user's information
- **Headers**: `Authorization: Bearer <token>`
- **Response** (200 OK):
  ```json
  {
    "user": {
      "id": 1,
      "username": "johndoe",
      "email": "john@example.com"
    }
  }
  ```

### Notes Endpoints (`/api/notes`)

#### List Notes
- **Method**: `GET`
- **Endpoint**: `/api/notes`
- **Description**: Retrieve paginated list of user's notes with optional filtering
- **Headers**: `Authorization: Bearer <token>`
- **Query Parameters**:
  - `page` (integer, default: 1): Page number
  - `per_page` (integer, default: 10, max: 100): Items per page
  - `status` (string): Filter by status ('active' or 'archived')
- **Response** (200 OK):
  ```json
  {
    "notes": [
      {
        "id": 1,
        "title": "My First Note",
        "content": "This is the content of my note",
        "status": "active",
        "created_at": "2023-10-01T10:00:00Z",
        "updated_at": "2023-10-01T10:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 10,
      "total": 1,
      "pages": 1
    }
  }
  ```

#### Create Note
- **Method**: `POST`
- **Endpoint**: `/api/notes`
- **Description**: Create a new note for the authenticated user
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**:
  ```json
  {
    "title": "New Note Title",
    "content": "Note content here",
    "status": "active"
  }
  ```
- **Response** (201 Created):
  ```json
  {
    "message": "Note created successfully",
    "note": {
      "id": 2,
      "title": "New Note Title",
      "content": "Note content here",
      "status": "active",
      "created_at": "2023-10-01T11:00:00Z",
      "updated_at": "2023-10-01T11:00:00Z"
    }
  }
  ```

#### Get Single Note
- **Method**: `GET`
- **Endpoint**: `/api/notes/{id}`
- **Description**: Retrieve a specific note by ID (ownership check enforced)
- **Headers**: `Authorization: Bearer <token>`
- **Response** (200 OK):
  ```json
  {
    "note": {
      "id": 1,
      "title": "My First Note",
      "content": "This is the content of my note",
      "status": "active",
      "created_at": "2023-10-01T10:00:00Z",
      "updated_at": "2023-10-01T10:00:00Z"
    }
  }
  ```

#### Update Note
- **Method**: `PATCH`
- **Endpoint**: `/api/notes/{id}`
- **Description**: Update an existing note (ownership check enforced)
- **Headers**: `Authorization: Bearer <token>`
- **Request Body** (partial update allowed):
  ```json
  {
    "title": "Updated Note Title",
    "status": "archived"
  }
  ```
- **Response** (200 OK):
  ```json
  {
    "message": "Note updated successfully",
    "note": {
      "id": 1,
      "title": "Updated Note Title",
      "content": "This is the content of my note",
      "status": "archived",
      "created_at": "2023-10-01T10:00:00Z",
      "updated_at": "2023-10-01T11:30:00Z"
    }
  }
  ```

#### Delete Note
- **Method**: `DELETE`
- **Endpoint**: `/api/notes/{id}`
- **Description**: Delete a note (ownership check enforced)
- **Headers**: `Authorization: Bearer <token>`
- **Response** (200 OK):
  ```json
  {
    "message": "Note deleted successfully"
  }
  ```

### Error Responses
All endpoints return standardized error responses:
```json
{
  "error": "Error code",
  "message": "Human-readable error message",
  "details": {} // Optional additional error details
}
```

Common error codes:
- `VALIDATION_ERROR`: Invalid input data
- `AUTHENTICATION_ERROR`: Invalid or missing token
- `AUTHORIZATION_ERROR`: Access denied (ownership violation)
- `NOT_FOUND`: Resource not found
- `INTERNAL_ERROR`: Server error

## Testing Routes with Postman

Postman is an excellent tool for testing REST APIs. Follow these step-by-step instructions to test the application's endpoints.

### Step 1: Import API Collection (Optional)
While you can manually create requests, consider importing a Postman collection for pre-configured requests.

### Step 2: Set Up Environment Variables
1. In Postman, create a new environment called "Notes App"
2. Add the following variables:
   - `base_url`: `http://localhost:5000`
   - `token`: (leave empty initially)

### Step 3: Test User Registration
1. Create a new request: `POST {{base_url}}/api/auth/signup`
2. Set headers: `Content-Type: application/json`
3. Set body to raw JSON:
   ```json
   {
     "username": "testuser",
     "email": "test@example.com",
     "password": "password123"
   }
   ```
4. Click "Send"
5. Expected: 201 Created response with user data and JWT token
6. Copy the token from response and set it as the `token` environment variable

### Step 4: Test User Login
1. Create a new request: `POST {{base_url}}/api/auth/login`
2. Set headers: `Content-Type: application/json`
3. Set body:
   ```json
   {
     "email": "test@example.com",
     "password": "password123"
   }
   ```
4. Click "Send"
5. Expected: 200 OK with user data and new token
6. Update the environment `token` variable

### Step 5: Test Protected Endpoints
For all subsequent requests, add the Authorization header:
- Header: `Authorization`
- Value: `Bearer {{token}}`

### Step 6: Create a Note
1. Create request: `POST {{base_url}}/api/notes`
2. Headers: `Content-Type: application/json`, `Authorization: Bearer {{token}}`
3. Body:
   ```json
   {
     "title": "My Test Note",
     "content": "This is a test note created via Postman",
     "status": "active"
   }
   ```
4. Expected: 201 Created with note data

### Step 7: List Notes
1. Create request: `GET {{base_url}}/api/notes`
2. Headers: `Authorization: Bearer {{token}}`
3. Optional query params: `?page=1&per_page=10&status=active`
4. Expected: 200 OK with notes array and pagination info

### Step 8: Update a Note
1. Create request: `PATCH {{base_url}}/api/notes/{note_id}` (replace {note_id} with actual ID)
2. Headers: `Content-Type: application/json`, `Authorization: Bearer {{token}}`
3. Body:
   ```json
   {
     "title": "Updated Note Title",
     "status": "archived"
   }
   ```
4. Expected: 200 OK with updated note data

### Step 9: Test User Profile
1. Create request: `GET {{base_url}}/api/auth/me`
2. Headers: `Authorization: Bearer {{token}}`
3. Expected: 200 OK with current user info

### Step 10: Test Logout
1. Create request: `POST {{base_url}}/api/auth/logout`
2. Headers: `Authorization: Bearer {{token}}`
3. Expected: 200 OK with logout message
4. Try accessing a protected endpoint - should return 401 Unauthorized

### Screenshots Descriptions
- **Registration Request/Response**: Shows the signup form and successful creation response with token
- **Login Request/Response**: Displays login credentials and authentication response
- **Notes List**: Illustrates paginated notes response with metadata
- **Create Note**: Demonstrates note creation request and confirmation response
- **Error Handling**: Shows validation error response for malformed requests

### Testing Tips
- Use Postman's "Tests" tab to automatically set environment variables from responses
- Create a test user first, then use that for all operations
- Test error scenarios by sending invalid data or missing tokens
- Use the "Runner" feature to execute the entire collection sequentially

## Testing Instructions

### Backend Testing

The backend includes comprehensive unit and integration tests using pytest.

1. **Navigate to backend directory:**
   ```bash
   cd backend
   pipenv shell
   ```

2. **Run all tests:**
   ```bash
   pytest
   ```

3. **Run specific test files:**
   ```bash
   pytest tests/test_auth.py
   pytest tests/test_notes.py
   ```

4. **Run tests with coverage:**
   ```bash
   pytest --cov=app --cov-report=html
   ```

5. **Run tests in verbose mode:**
   ```bash
   pytest -v
   ```

### Test Coverage
- **Authentication Tests**: User registration, login validation, token verification, logout functionality
- **Notes CRUD Tests**: Create, read, update, delete operations with ownership validation
- **Security Tests**: Authorization checks, input validation, error handling
- **Integration Tests**: Full request/response cycles with database interactions

### Frontend Testing

The frontend uses vanilla JavaScript without a formal testing framework. Manual testing is recommended:

1. **Functional Testing**:
   - Test user registration and login flows
   - Verify note creation, editing, and deletion
   - Check pagination and filtering functionality
   - Test responsive design on different screen sizes

2. **Cross-Browser Testing**:
   - Test on Chrome, Firefox, Safari, and Edge
   - Verify functionality on mobile devices

3. **User Experience Testing**:
   - Test form validation and error messages
   - Verify loading states and feedback messages
   - Check accessibility with keyboard navigation

## Demo Credentials and Usage

### Demo User Accounts
After running the seed script (`python seed.py`), the following demo accounts are available:

- **Username**: demo_user
- **Email**: demo@example.com
- **Password**: demopass123

- **Username**: test_user
- **Email**: test@example.com
- **Password**: testpass123

### Usage Guide

1. **Access the Application**: Open `http://localhost:3000` in your browser
2. **Register or Login**: Use the demo credentials or create a new account
3. **Dashboard**: After login, you'll see your personal dashboard with note management options
4. **Create Notes**: Click "Add Note" to create new notes with titles and content
5. **Manage Notes**: Use the edit/delete buttons to modify existing notes
6. **Filter Notes**: Use the status filter to view active or archived notes
7. **Pagination**: Navigate through multiple pages of notes using pagination controls

### Application Flow
1. **Authentication**: User logs in → JWT token stored → Protected routes accessible
2. **Note Management**: User creates notes → Data sent to API → Stored in database with user association
3. **Data Retrieval**: Frontend requests notes → API validates token → Returns user-owned notes with pagination
4. **State Management**: Frontend maintains local state → Updates UI dynamically without page reloads

## Security Features

### Authentication & Authorization
- **JWT Tokens**: Stateless authentication with configurable expiration (168 hours default)
- **Password Hashing**: bcrypt hashing prevents plaintext password storage
- **Token Revocation**: Blocklist system enables secure logout and prevents token reuse
- **Ownership Validation**: All note operations verify user ownership before allowing access

### Input Validation & Sanitization
- **Schema Validation**: Marshmallow schemas validate all input data with detailed error messages
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **XSS Protection**: Input validation prevents malicious script injection
- **Rate Limiting**: Consider implementing rate limiting for production deployment

### Data Protection
- **Encrypted Passwords**: bcrypt with salt for secure password storage
- **CORS Configuration**: Restricted cross-origin access to prevent unauthorized requests
- **Environment Variables**: Sensitive configuration stored securely outside codebase
- **Database Security**: Foreign key constraints and cascade operations maintain data integrity

### Security Best Practices
- **HTTPS**: Always use HTTPS in production for encrypted data transmission
- **Secure Headers**: Implement security headers (CSP, HSTS, etc.) in production
- **Logging**: Implement proper logging for security monitoring
- **Regular Updates**: Keep dependencies updated to address security vulnerabilities

## Deployment Guidelines

### Production Environment Setup

1. **Server Configuration**:
   - Use a production WSGI server like Gunicorn or uWSGI
   - Configure reverse proxy with Nginx
   - Set up SSL/TLS certificates for HTTPS

2. **Database Migration**:
   - Switch from SQLite to PostgreSQL or MySQL
   - Update `SQLALCHEMY_DATABASE_URI` in production config
   - Run database migrations: `flask db upgrade`

3. **Environment Variables**:
   - Set strong, unique secret keys for `SECRET_KEY` and `JWT_SECRET_KEY`
   - Configure `CORS_ORIGINS` to your frontend domain only
   - Set `FLASK_ENV=production`

4. **Security Hardening**:
   - Enable HTTPS and security headers
   - Configure firewall rules
   - Set up monitoring and logging
   - Implement backup strategies

### Deployment Platforms

#### Heroku Deployment
1. Create a `Procfile`:
   ```
   web: gunicorn run:app
   ```
2. Configure environment variables in Heroku dashboard
3. Deploy using Heroku CLI or Git integration

#### Docker Deployment
1. Create `Dockerfile` and `docker-compose.yml`
2. Build and run containers:
   ```bash
   docker-compose up -d
   ```

#### AWS/GCP/Azure
1. Use Elastic Beanstalk, App Engine, or App Service
2. Configure managed database services
3. Set up load balancers and auto-scaling

### Performance Optimization
- **Database Indexing**: Ensure proper indexes on frequently queried columns
- **Caching**: Implement Redis for session storage and caching
- **CDN**: Use CDN for static assets
- **Monitoring**: Set up application performance monitoring

## Contributing

We welcome contributions to the Full-Stack Notes Application! Please follow these guidelines:

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes with proper tests
4. Ensure all tests pass: `pytest`
5. Follow the existing code style and conventions
6. Update documentation as needed

### Code Standards
- **Backend**: Follow PEP 8 Python style guidelines
- **Frontend**: Use consistent JavaScript/ES6 patterns
- **Commits**: Write clear, descriptive commit messages
- **Tests**: Maintain high test coverage for new features

### Pull Request Process
1. Ensure your branch is up-to-date with main
2. Run the full test suite
3. Update this README if your changes affect usage or API
4. Create a pull request with a clear description of changes
5. Address any review feedback

### Reporting Issues
- Use the GitHub issue tracker for bugs and feature requests
- Provide detailed steps to reproduce issues
- Include relevant environment information

## License

This project is licensed under the MIT License - see the LICENSE file for details.

The MIT License allows for free use, modification, and distribution of the software, provided that the original copyright notice and disclaimer are included in all copies or substantial portions of the software.

---

**Note**: This application is designed for educational and portfolio purposes. For production use, additional security measures, performance optimizations, and scalability considerations should be implemented.</content>
<parameter name="filePath">/home/kyp/moringa/Full-Auth-Flask-Backend--Productivity-App/README.md