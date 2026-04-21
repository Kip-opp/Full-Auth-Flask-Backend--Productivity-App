import pool from '../config/database.js';
import bcrypt from 'bcryptjs';

export class User {
  static async create(email, password, name) {
    const hashedPassword = await bcrypt.hash(password, 10);
    const [result] = await pool.execute(
      'INSERT INTO users (email, password, name) VALUES (?, ?, ?)',
      [email, hashedPassword, name]
    );
    return result.insertId;
  }

  static async findByEmail(email) {
    const [rows] = await pool.execute(
      'SELECT * FROM users WHERE email = ?',
      [email]
    );
    return rows[0];
  }

  static async findById(id) {
    const [rows] = await pool.execute(
      'SELECT id, email, name, createdAt FROM users WHERE id = ?',
      [id]
    );
    return rows[0];
  }

  static async verifyPassword(password, hashedPassword) {
    return await bcrypt.compare(password, hashedPassword);
  }
}

export default User;