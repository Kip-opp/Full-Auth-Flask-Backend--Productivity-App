import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import authRoutes from './routes/auth.js';
import notesRoutes from './routes/notes.js';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors({ origin: process.env.CORS_ORIGIN || 'http://localhost:5173' }));
app.use(express.json());

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/notes', notesRoutes);

// Health check
app.get('/api/health', (req, res) => {
  res.json({ success: true, message: 'Server is running' });
});

// Error handling
app.use((err, req, res, next) => {
  console.error(err);
  res.status(500).json({
    success: false,
    error: { code: 'INTERNAL_SERVER_ERROR', message: 'Something went wrong' },
  });
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});