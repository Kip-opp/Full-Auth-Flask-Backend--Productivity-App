import express from 'express';
import { body, param } from 'express-validator';
import {
  createNote,
  getNotes,
  getNote,
  updateNote,
  deleteNote,
} from '../controllers/notesController.js';
import authMiddleware from '../middleware/auth.js';

const router = express.Router();

router.use(authMiddleware);

router.post(
  '/',
  [
    body('title').notEmpty().isLength({ max: 255 }).withMessage('Title is required and must be less than 255 characters'),
    body('content').notEmpty().withMessage('Content is required'),
    body('status').optional().isIn(['active', 'archived']).withMessage('Invalid status'),
  ],
  createNote
);

router.get('/', getNotes);

router.get(
  '/:id',
  [param('id').isInt().withMessage('Invalid note ID')],
  getNote
);

router.patch(
  '/:id',
  [
    param('id').isInt().withMessage('Invalid note ID'),
    body('title').optional().isLength({ max: 255 }).withMessage('Title must be less than 255 characters'),
    body('content').optional().notEmpty().withMessage('Content cannot be empty'),
    body('status').optional().isIn(['active', 'archived']).withMessage('Invalid status'),
  ],
  updateNote
);

router.delete(
  '/:id',
  [param('id').isInt().withMessage('Invalid note ID')],
  deleteNote
);

export default router;