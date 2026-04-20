from datetime import datetime, timedelta
from app import create_app
from app.extensions import db, bcrypt
from app.models.user import User
from app.models.todo import Todo

app = create_app()

with app.app_context():
    demo_user = User.query.filter_by(email="demo@example.com").first()
    if not demo_user:
        demo_user = User(
            username="demo",
            email="demo@example.com",
            password_hash=bcrypt.generate_password_hash("password123").decode("utf-8")
        )
        db.session.add(demo_user)

    kyp_user = User.query.filter_by(email="kyp@example.com").first()
    if not kyp_user:
        kyp_user = User(
            username="kyp",
            email="kyp@example.com",
            password_hash=bcrypt.generate_password_hash("12345678").decode("utf-8")
        )
        db.session.add(kyp_user)

    db.session.commit()

    if not Todo.query.filter_by(user_id=demo_user.id).first():
        demo_todos = [
            Todo(
                title="Finish backend authentication",
                description="Complete signup, login, and me endpoints",
                notes="Test all auth endpoints in Postman and browser frontend.",
                priority="high",
                due_date=datetime.utcnow() + timedelta(days=1),
                completed=False,
                user_id=demo_user.id
            ),
            Todo(
                title="Build notes UI",
                description="Add frontend form for notes and todo updates",
                notes="Make sure notes save through PATCH and display on cards.",
                priority="medium",
                due_date=datetime.utcnow() + timedelta(days=3),
                completed=False,
                user_id=demo_user.id
            )
        ]
        db.session.add_all(demo_todos)

    if not Todo.query.filter_by(user_id=kyp_user.id).first():
        kyp_todos = [
            Todo(
                title="Prepare submission README",
                description="Write installation, endpoint list, and setup steps",
                notes="Sync demo accounts and document all current routes.",
                priority="high",
                due_date=datetime.utcnow() + timedelta(days=2),
                completed=False,
                user_id=kyp_user.id
            ),
            Todo(
                title="Review protected routes",
                description="Ensure users only access their own records",
                notes="Test with both demo and kyp accounts.",
                priority="medium",
                due_date=datetime.utcnow() - timedelta(days=1),
                completed=False,
                user_id=kyp_user.id
            )
        ]
        db.session.add_all(kyp_todos)

    db.session.commit()

    print("Seed completed successfully.")
    print("Demo user: demo@example.com / password123")
    print("Kyp user: kyp@example.com / 12345678")