import pool from '../config/database.js';

export class Note {
  static async create(userId, title, content, status = 'active') {
    const [result] = await pool.execute(
      'INSERT INTO notes (userId, title, content, status) VALUES (?, ?, ?, ?)',
      [userId, title, content, status]
    );
    return result.insertId;
  }

  static async findById(id, userId) {
    const [rows] = await pool.execute(
      'SELECT * FROM notes WHERE id = ? AND userId = ?',
      [id, userId]
    );
    return rows[0];
  }

  static async findByUserId(userId, page = 1, perPage = 10, status = null) {
    const offset = (page - 1) * perPage;
    let query = 'SELECT * FROM notes WHERE userId = ?';
    let countQuery = 'SELECT COUNT(*) as total FROM notes WHERE userId = ?';
    let params = [userId];

    if (status) {
      query += ' AND status = ?';
      countQuery += ' AND status = ?';
      params.push(status);
    }

    query += ' ORDER BY createdAt DESC LIMIT ? OFFSET ?';
    const [rows] = await pool.execute(query, [...params, perPage, offset]);

    const [countResult] = await pool.execute(countQuery, params);
    const total = countResult[0].total;

    return {
      items: rows,
      total,
      page,
      perPage,
      pages: Math.ceil(total / perPage),
    };
  }

  static async update(id, userId, title, content, status) {
    const updates = [];
    const values = [];

    if (title !== undefined) {
      updates.push('title = ?');
      values.push(title);
    }
    if (content !== undefined) {
      updates.push('content = ?');
      values.push(content);
    }
    if (status !== undefined) {
      updates.push('status = ?');
      values.push(status);
    }

    updates.push('updatedAt = NOW()');
    values.push(id, userId);

    const query = `UPDATE notes SET ${updates.join(', ')} WHERE id = ? AND userId = ?`;
    const [result] = await pool.execute(query, values);
    return result.affectedRows > 0;
  }

  static async delete(id, userId) {
    const [result] = await pool.execute(
      'DELETE FROM notes WHERE id = ? AND userId = ?',
      [id, userId]
    );
    return result.affectedRows > 0;
  }
}

export default Note;