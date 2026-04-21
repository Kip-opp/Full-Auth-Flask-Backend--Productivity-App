# Standalone Full-Stack Notes Application

A complete, production-ready Notes application with JWT authentication, user-owned CRUD operations, pagination, and a polished dashboard. This application runs entirely locally without any platform dependencies.

## Features

✅ User authentication (signup, login, logout)
✅ JWT token management with server-side revocation
✅ Complete notes CRUD with ownership enforcement
✅ Pagination with page, perPage, and status filtering
✅ Input validation and standardized responses
✅ MySQL database integration
✅ Responsive dashboard UI
✅ Create, read, update, delete notes
✅ Filter notes by status (active/archived)
✅ Demo users and sample data

## Tech Stack

### Backend
- Node.js + Express
- MySQL database
- JWT authentication with bcrypt
- Express-validator for input validation
- CORS enabled

### Frontend
- React 18 with Vite
- Axios for API calls
- Modern CSS with responsive design
- Local storage for token persistence

## Project Structure

```
notes-app/
├── backend/
│   ├── config/database.js
│   ├── models/
│   │   ├── User.js
│   │   ├── Note.js
│   │   └── TokenBlocklist.js
│   ├── routes/
│   │   ├── auth.js
│   │   └── notes.js
│   ├── middleware/auth.js
│   ├── controllers/
│   │   ├── authController.js
│   │   └── notesController.js
│   ├── server.js
│   ├── package.json
│   └── .env.example
├── frontend/
│   ├── public/index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── NotesList.jsx
│   │   │   ├── NoteForm.jsx
│   │   │   └── Auth.jsx
│   │   ├── services/api.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
├── database/schema.sql
├── seed/seed.js
└── README.md
```

## Quick Start

### Prerequisites
- Node.js 16+
- MySQL 8.0+
- npm or yarn

### 1. Setup Database
```bash
# Create database
mysql -u root -p < database/schema.sql
```

### 2. Setup Backend
```bash
cd backend
npm install
cp .env.example .env
# Edit .env with your MySQL credentials
npm run seed
npm run dev
```

### 3. Setup Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

### 4. Access Application
Open `http://localhost:5173` in your browser.

## Demo Credentials

After running the seed script, use these accounts:

- **alice@example.com** / password123 (5 sample notes)
- **bob@example.com** / password123 (3 sample notes)

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/auth/signup` | Register new user | No |
| POST | `/api/auth/login` | Login user | No |
| POST | `/api/auth/logout` | Logout user | Yes |
| GET | `/api/auth/me` | Get current user | Yes |
| GET | `/api/notes` | List user notes | Yes |
| GET | `/api/notes/:id` | Get single note | Yes |
| POST | `/api/notes` | Create note | Yes |
| PATCH | `/api/notes/:id` | Update note | Yes |
| DELETE | `/api/notes/:id` | Delete note | Yes |

## Environment Configuration

### Backend (.env)
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=notes_app
PORT=5000
NODE_ENV=development
JWT_SECRET=your_super_secret_jwt_key
JWT_EXPIRY=7d
CORS_ORIGIN=http://localhost:5173
```

### Frontend (.env)
```env
VITE_API_URL=http://localhost:5000/api
```

## Database Schema

The application uses three main tables:

- **users**: User accounts with email/password
- **notes**: User notes with title, content, status
- **tokenBlocklist**: Revoked JWT tokens

Run `database/schema.sql` to create the database structure.

## Running Tests

```bash
# Backend tests (if implemented)
cd backend && npm test

# Frontend tests (if implemented)
cd frontend && npm test
```

## Features Overview

### Authentication
- Secure signup with email validation
- Password hashing with bcrypt
- JWT token generation and verification
- Server-side token revocation on logout

### Notes Management
- Create notes with title, content, and status
- Edit existing notes
- Delete notes with confirmation
- Filter by active/archived status
- Paginated results (10 per page)

### Security
- User ownership enforced on all note operations
- Input validation and sanitization
- CORS protection
- JWT token expiration
- Password strength requirements

### UI/UX
- Responsive design for mobile/desktop
- Loading states and error handling
- Form validation feedback
- Clean, modern interface

## Development

### Backend Development
```bash
cd backend
npm run dev  # Runs with nodemon for auto-restart
```

### Frontend Development
```bash
cd frontend
npm run dev  # Vite dev server with hot reload
```

### Database Changes
Modify `database/schema.sql` and run:
```bash
mysql -u root -p notes_app < database/schema.sql
```

## Deployment

### Backend Deployment
1. Set production environment variables
2. Run `npm run seed` for initial data
3. Start with `npm start`

### Frontend Deployment
1. Build for production: `npm run build`
2. Serve static files from `dist/` directory

## Troubleshooting

### Database Connection Issues
- Ensure MySQL is running
- Check credentials in `.env`
- Verify database exists

### CORS Errors
- Confirm `CORS_ORIGIN` matches frontend URL
- Check browser network tab for preflight errors

### Authentication Issues
- Verify JWT_SECRET is set
- Check token expiration settings
- Ensure correct Authorization header format

### Port Conflicts
- Backend defaults to 5000, frontend to 5173
- Change in respective `.env` files if needed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - feel free to use this project for learning and development.