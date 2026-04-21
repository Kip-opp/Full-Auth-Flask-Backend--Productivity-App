import pool from '../config/database.js';

export class TokenBlocklist {
  static async add(token, userId, expiresAt) {
    await pool.execute(
      'INSERT INTO tokenBlocklist (token, userId, expiresAt) VALUES (?, ?, ?)',
      [token, userId, expiresAt]
    );
  }

  static async isBlocked(token) {
    const [rows] = await pool.execute(
      'SELECT * FROM tokenBlocklist WHERE token = ?',
      [token]
    );
    return rows.length > 0;
  }

  static async cleanup() {
    await pool.execute('DELETE FROM tokenBlocklist WHERE expiresAt < NOW()');
  }
}

export default TokenBlocklist;