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

        demo_user = User(
            username='demo_user',
            email='demo@example.com'
        )
        demo_user.set_password('demopass123')

        test_user = User(
            username='test_user',
            email='test@example.com'
        )
        test_user.set_password('testpass123')

        db.session.add(demo_user)
        db.session.add(test_user)
        db.session.commit()

        print(f'✅ Created users: demo_user, test_user')

        demo_notes = [
            Note(
                user_id=demo_user.id,
                title='Project Planning',
                content='Outline for Q2 roadmap and feature prioritization.',
                status='active'
            ),
            Note(
                user_id=demo_user.id,
                title='Meeting Notes',
                content='Discussed sprint planning and team capacity.',
                status='active'
            ),
            Note(
                user_id=demo_user.id,
                title='UI Improvements',
                content='Ideas for improving user interface and experience.',
                status='active'
            ),
            Note(
                user_id=demo_user.id,
                title='Learning Resources',
                content='React and TypeScript guides for team development.',
                status='archived'
            ),
            Note(
                user_id=demo_user.id,
                title='Personal Goals',
                content='Career development objectives for 2024.',
                status='active'
            ),
        ]

        for note in demo_notes:
            db.session.add(note)

        test_notes = [
            Note(
                user_id=test_user.id,
                title='Database Schema',
                content='Current database schema design and optimization.',
                status='active'
            ),
            Note(
                user_id=test_user.id,
                title='API Documentation',
                content='Endpoints to document and API reference guide.',
                status='active'
            ),
            Note(
                user_id=test_user.id,
                title='Deployment Checklist',
                content='Pre-deployment tasks and verification steps.',
                status='archived'
            ),
        ]

        for note in test_notes:
            db.session.add(note)

        db.session.commit()

        print(f'✅ Created {len(demo_notes)} notes for demo_user')
        print(f'✅ Created {len(test_notes)} notes for test_user')
        print('\n📝 Demo Credentials:')
        print('   demo@example.com / demopass123')
        print('   test@example.com / testpass123')
        print('\n✨ Database seeding complete!')


if __name__ == '__main__':
    seed_database()