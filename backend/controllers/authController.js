import User from '../models/User.js';
import TokenBlocklist from '../models/TokenBlocklist.js';
import jwt from 'jsonwebtoken';
import { validationResult } from 'express-validator';

export const signup = async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        success: false,
        error: { code: 'BAD_REQUEST', message: errors.array()[0].msg },
      });
    }

    const { email, password, name } = req.body;

    // Check if user exists
    const existingUser = await User.findByEmail(email);
    if (existingUser) {
      return res.status(400).json({
        success: false,
        error: { code: 'BAD_REQUEST', message: 'Email already registered' },
      });
    }

    const userId = await User.create(email, password, name);
    const user = await User.findById(userId);

    const token = jwt.sign(
      { id: user.id, email: user.email },
      process.env.JWT_SECRET,
      { expiresIn: process.env.JWT_EXPIRY }
    );

    return res.status(201).json({
      success: true,
      message: 'User registered successfully',
      data: { user, token },
    });
  } catch (error) {
    console.error('Signup error:', error);
    return res.status(500).json({
      success: false,
      error: { code: 'INTERNAL_SERVER_ERROR', message: 'Signup failed' },
    });
  }
};

export const login = async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        success: false,
        error: { code: 'BAD_REQUEST', message: errors.array()[0].msg },
      });
    }

    const { email, password } = req.body;

    const user = await User.findByEmail(email);
    if (!user) {
      return res.status(401).json({
        success: false,
        error: { code: 'UNAUTHORIZED', message: 'Invalid credentials' },
      });
    }

    const isValidPassword = await User.verifyPassword(password, user.password);
    if (!isValidPassword) {
      return res.status(401).json({
        success: false,
        error: { code: 'UNAUTHORIZED', message: 'Invalid credentials' },
      });
    }

    const token = jwt.sign(
      { id: user.id, email: user.email },
      process.env.JWT_SECRET,
      { expiresIn: process.env.JWT_EXPIRY }
    );

    const userData = {
      id: user.id,
      email: user.email,
      name: user.name,
      createdAt: user.createdAt,
    };

    return res.json({
      success: true,
      message: 'Login successful',
      data: { user: userData, token },
    });
  } catch (error) {
    console.error('Login error:', error);
    return res.status(500).json({
      success: false,
      error: { code: 'INTERNAL_SERVER_ERROR', message: 'Login failed' },
    });
  }
};

export const logout = async (req, res) => {
  try {
    const token = req.headers.authorization?.split(' ')[1];
    if (token) {
      const decoded = jwt.decode(token);
      if (decoded && decoded.exp) {
        const expiresAt = new Date(decoded.exp * 1000);
        await TokenBlocklist.add(token, req.user.id, expiresAt);
      }
    }

    return res.json({
      success: true,
      message: 'Logout successful',
    });
  } catch (error) {
    console.error('Logout error:', error);
    return res.status(500).json({
      success: false,
      error: { code: 'INTERNAL_SERVER_ERROR', message: 'Logout failed' },
    });
  }
};

export const me = async (req, res) => {
  try {
    const user = await User.findById(req.user.id);
    if (!user) {
      return res.status(404).json({
        success: false,
        error: { code: 'NOT_FOUND', message: 'User not found' },
      });
    }

    return res.json({
      success: true,
      user,
    });
  } catch (error) {
    console.error('Me error:', error);
    return res.status(500).json({
      success: false,
      error: { code: 'INTERNAL_SERVER_ERROR', message: 'Failed to fetch user' },
    });
  }
};