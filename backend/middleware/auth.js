import jwt from 'jsonwebtoken';
import TokenBlocklist from '../models/TokenBlocklist.js';

export const authMiddleware = async (req, res, next) => {
  try {
    const token = req.headers.authorization?.split(' ')[1];

    if (!token) {
      return res.status(401).json({
        success: false,
        error: { code: 'UNAUTHORIZED', message: 'No token provided' },
      });
    }

    // Check if token is blocked
    const isBlocked = await TokenBlocklist.isBlocked(token);
    if (isBlocked) {
      return res.status(401).json({
        success: false,
        error: { code: 'UNAUTHORIZED', message: 'Token has been revoked' },
      });
    }

    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;
    next();
  } catch (error) {
    return res.status(401).json({
      success: false,
      error: { code: 'UNAUTHORIZED', message: 'Invalid token' },
    });
  }
};

export default authMiddleware;