from datetime import datetime, timedelta
from app import create_app
from app.extensions import db, bcrypt
from app.models.user import User
from app.models.todo import Todo

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    demo_user = User(
        username="demo",
        email="demo@example.com",
        password_hash=bcrypt.generate_password_hash("password123").decode("utf-8"),
    )

    notes_user = User(
        username="kyp",
        email="kyp@example.com",
        password_hash=bcrypt.generate_password_hash("12345678").decode("utf-8"),
    )

    db.session.add_all([demo_user, notes_user])
    db.session.commit()

    todos = [
        Todo(
            title="Finish backend authentication",
            description="Complete signup, login, and me endpoints",
            notes="Test all auth endpoints in Postman and browser frontend.",
            priority="high",
            due_date=datetime.utcnow() + timedelta(days=1),
            completed=False,
            user_id=demo_user.id,
        ),
        Todo(
            title="Build notes UI",
            description="Add frontend form for notes and todo updates",
            notes="Make sure notes save through PATCH and display on cards.",
            priority="medium",
            due_date=datetime.utcnow() + timedelta(days=3),
            completed=False,
            user_id=demo_user.id,
        ),
        Todo(
            title="Prepare submission README",
            description="Write installation, run steps, and endpoint list",
            notes="Double-check rubric before final push.",
            priority="high",
            due_date=datetime.utcnow() + timedelta(days=2),
            completed=False,
            user_id=notes_user.id,
        ),
        Todo(
            title="Review protected routes",
            description="Ensure users only access their own records",
            notes="Test with demo@example.com and kyp@example.com separately.",
            priority="high",
            due_date=datetime.utcnow() - timedelta(days=1),
            completed=False,
            user_id=notes_user.id,
        ),
    ]

    db.session.add_all(todos)
    db.session.commit()

    print("Database seeded successfully.")
    print("demo@example.com / password123")
    print("kyp@example.com / 12345678")
