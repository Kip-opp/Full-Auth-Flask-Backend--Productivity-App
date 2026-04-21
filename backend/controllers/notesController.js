import Note from '../models/Note.js';
import { validationResult } from 'express-validator';

export const createNote = async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        success: false,
        error: { code: 'BAD_REQUEST', message: errors.array()[0].msg },
      });
    }

    const { title, content, status } = req.body;
    const noteId = await Note.create(req.user.id, title, content, status);
    const note = await Note.findById(noteId, req.user.id);

    return res.status(201).json({
      success: true,
      message: 'Note created successfully',
      data: note,
    });
  } catch (error) {
    console.error('Create note error:', error);
    return res.status(500).json({
      success: false,
      error: { code: 'INTERNAL_SERVER_ERROR', message: 'Failed to create note' },
    });
  }
};

export const getNotes = async (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const perPage = parseInt(req.query.perPage) || 10;
    const status = req.query.status || null;

    if (page < 1 || perPage < 1 || perPage > 100) {
      return res.status(400).json({
        success: false,
        error: { code: 'BAD_REQUEST', message: 'Invalid pagination parameters' },
      });
    }

    const result = await Note.findByUserId(req.user.id, page, perPage, status);

    return res.json({
      success: true,
      data: result,
    });
  } catch (error) {
    console.error('Get notes error:', error);
    return res.status(500).json({
      success: false,
      error: { code: 'INTERNAL_SERVER_ERROR', message: 'Failed to fetch notes' },
    });
  }
};

export const getNote = async (req, res) => {
  try {
    const { id } = req.params;
    const note = await Note.findById(id, req.user.id);

    if (!note) {
      return res.status(404).json({
        success: false,
        error: { code: 'NOT_FOUND', message: 'Note not found' },
      });
    }

    return res.json({
      success: true,
      data: note,
    });
  } catch (error) {
    console.error('Get note error:', error);
    return res.status(500).json({
      success: false,
      error: { code: 'INTERNAL_SERVER_ERROR', message: 'Failed to fetch note' },
    });
  }
};

export const updateNote = async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        success: false,
        error: { code: 'BAD_REQUEST', message: errors.array()[0].msg },
      });
    }

    const { id } = req.params;
    const { title, content, status } = req.body;

    const existing = await Note.findById(id, req.user.id);
    if (!existing) {
      return res.status(404).json({
        success: false,
        error: { code: 'NOT_FOUND', message: 'Note not found' },
      });
    }

    await Note.update(id, req.user.id, title, content, status);
    const updated = await Note.findById(id, req.user.id);

    return res.json({
      success: true,
      message: 'Note updated successfully',
      data: updated,
    });
  } catch (error) {
    console.error('Update note error:', error);
    return res.status(500).json({
      success: false,
      error: { code: 'INTERNAL_SERVER_ERROR', message: 'Failed to update note' },
    });
  }
};

export const deleteNote = async (req, res) => {
  try {
    const { id } = req.params;

    const existing = await Note.findById(id, req.user.id);
    if (!existing) {
      return res.status(404).json({
        success: false,
        error: { code: 'NOT_FOUND', message: 'Note not found' },
      });
    }

    await Note.delete(id, req.user.id);

    return res.json({
      success: true,
      message: 'Note deleted successfully',
    });
  } catch (error) {
    console.error('Delete note error:', error);
    return res.status(500).json({
      success: false,
      error: { code: 'INTERNAL_SERVER_ERROR', message: 'Failed to delete note' },
    });
  }
};