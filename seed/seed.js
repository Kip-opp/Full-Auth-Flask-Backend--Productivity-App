import mysql from 'mysql2/promise';
import bcrypt from 'bcryptjs';
import dotenv from 'dotenv';

dotenv.config();

async function seed() {
  const connection = await mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME,
  });

  try {
    console.log('Seeding database...');

    // Create demo users
    const hashedPassword1 = await bcrypt.hash('password123', 10);
    const hashedPassword2 = await bcrypt.hash('password123', 10);

    await connection.execute(
      'INSERT IGNORE INTO users (email, password, name) VALUES (?, ?, ?)',
      ['alice@example.com', hashedPassword1, 'Alice Johnson']
    );

    await connection.execute(
      'INSERT IGNORE INTO users (email, password, name) VALUES (?, ?, ?)',
      ['bob@example.com', hashedPassword2, 'Bob Smith']
    );

    // Get user IDs
    const [aliceRows] = await connection.execute(
      'SELECT id FROM users WHERE email = ?',
      ['alice@example.com']
    );
    const [bobRows] = await connection.execute(
      'SELECT id FROM users WHERE email = ?',
      ['bob@example.com']
    );

    const aliceId = aliceRows[0].id;
    const bobId = bobRows[0].id;

    // Create sample notes for Alice
    const aliceNotes = [
      { title: 'Project Planning', content: 'Outline for Q2 roadmap...', status: 'active' },
      { title: 'Meeting Notes', content: 'Discussed sprint planning...', status: 'active' },
      { title: 'Ideas', content: 'UI improvements to explore...', status: 'active' },
      { title: 'Learning Resources', content: 'React and TypeScript guides...', status: 'archived' },
      { title: 'Personal Goals', content: 'Career development for 2024...', status: 'active' },
    ];

    for (const note of aliceNotes) {
      await connection.execute(
        'INSERT INTO notes (userId, title, content, status) VALUES (?, ?, ?, ?)',
        [aliceId, note.title, note.content, note.status]
      );
    }

    // Create sample notes for Bob
    const bobNotes = [
      { title: 'Database Schema', content: 'Current schema design...', status: 'active' },
      { title: 'API Documentation', content: 'Endpoints to document...', status: 'active' },
      { title: 'Deployment Checklist', content: 'Pre-deployment tasks...', status: 'archived' },
    ];

    for (const note of bobNotes) {
      await connection.execute(
        'INSERT INTO notes (userId, title, content, status) VALUES (?, ?, ?, ?)',
        [bobId, note.title, note.content, note.status]
      );
    }

    console.log('✅ Database seeded successfully!');
    console.log('Demo users:');
    console.log('- alice@example.com (password: password123)');
    console.log('- bob@example.com (password: password123)');
  } catch (error) {
    console.error('❌ Seeding failed:', error);
  } finally {
    await connection.end();
  }
}

seed();