import express from 'express';
import { body } from 'express-validator';
import { signup, login, logout, me } from '../controllers/authController.js';
import authMiddleware from '../middleware/auth.js';

const router = express.Router();

router.post(
  '/signup',
  [
    body('email').isEmail().withMessage('Invalid email'),
    body('password').isLength({ min: 8 }).withMessage('Password must be at least 8 characters'),
    body('name').notEmpty().withMessage('Name is required'),
  ],
  signup
);

router.post(
  '/login',
  [
    body('email').isEmail().withMessage('Invalid email'),
    body('password').notEmpty().withMessage('Password is required'),
  ],
  login
);

router.post('/logout', authMiddleware, logout);
router.get('/me', authMiddleware, me);

export default router;