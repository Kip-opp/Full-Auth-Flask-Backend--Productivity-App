"""Database seeding script."""
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.note import Note
from app.config import DevelopmentConfig


def seed_database():
    """Seed database with demo users and notes."""
    app = create_app(DevelopmentConfig)
    
    with app.app_context():
        db.drop_all()
        db.create_all()

        print('🌱 Seeding database...')

        alice = User(
            username='alice',
            email='alice@example.com'
        )
        alice.set_password('password123')
        
        bob = User(
            username='bob',
            email='bob@example.com'
        )
        bob.set_password('password123')

        db.session.add(alice)
        db.session.add(bob)
        db.session.commit()

        print(f'✅ Created users: alice, bob')

        alice_notes = [
            Note(
                user_id=alice.id,
                title='Project Planning',
                content='Outline for Q2 roadmap and feature prioritization.',
                status='active'
            ),
            Note(
                user_id=alice.id,
                title='Meeting Notes',
                content='Discussed sprint planning and team capacity.',
                status='active'
            ),
            Note(
                user_id=alice.id,
                title='UI Improvements',
                content='Ideas for improving user interface and experience.',
                status='active'
            ),
            Note(
                user_id=alice.id,
                title='Learning Resources',
                content='React and TypeScript guides for team development.',
                status='archived'
            ),
            Note(
                user_id=alice.id,
                title='Personal Goals',
                content='Career development objectives for 2024.',
                status='active'
            ),
        ]

        for note in alice_notes:
            db.session.add(note)

        bob_notes = [
            Note(
                user_id=bob.id,
                title='Database Schema',
                content='Current database schema design and optimization.',
                status='active'
            ),
            Note(
                user_id=bob.id,
                title='API Documentation',
                content='Endpoints to document and API reference guide.',
                status='active'
            ),
            Note(
                user_id=bob.id,
                title='Deployment Checklist',
                content='Pre-deployment tasks and verification steps.',
                status='archived'
            ),
        ]

        for note in bob_notes:
            db.session.add(note)

        db.session.commit()

        print(f'✅ Created {len(alice_notes)} notes for alice')
        print(f'✅ Created {len(bob_notes)} notes for bob')
        print('\n📝 Demo Credentials:')
        print('   alice / password123')
        print('   bob / password123')
        print('\n✨ Database seeding complete!')


if __name__ == '__main__':
    seed_database()