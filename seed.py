from datetime import datetime, timedelta
from app import create_app
from app.extensions import db, bcrypt
from app.models.user import User
from app.models.todo import Todo

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    demo_password = bcrypt.generate_password_hash("password123").decode("utf-8")
    alice_password = bcrypt.generate_password_hash("alice123").decode("utf-8")

    demo_user = User(
        username="demo",
        email="demo@example.com",
        password_hash=demo_password
    )

    alice_user = User(
        username="alice",
        email="alice@example.com",
        password_hash=alice_password
    )

    db.session.add_all([demo_user, alice_user])
    db.session.commit()

    todos = [
        Todo(
            title="Finish project documentation",
            description="Write README and endpoint documentation",
            notes="Include installation, run steps, and Postman examples.",
            priority="high",
            due_date=datetime.utcnow() + timedelta(days=2),
            completed=False,
            user_id=demo_user.id
        ),
        Todo(
            title="Prepare presentation",
            description="Create talking points for backend demo",
            notes="Show signup, login, me, and todo pagination in Postman.",
            priority="medium",
            due_date=datetime.utcnow() + timedelta(days=4),
            completed=False,
            user_id=demo_user.id
        ),
        Todo(
            title="Study for exam",
            description="Revise JWT auth, bcrypt, and migrations",
            notes="Focus on protected routes and ownership checks.",
            priority="high",
            due_date=datetime.utcnow() - timedelta(days=1),
            completed=False,
            user_id=demo_user.id
        ),
        Todo(
            title="Buy groceries",
            description="Milk, bread, eggs, and fruit",
            notes="Check budget before ordering online.",
            priority="low",
            due_date=datetime.utcnow() + timedelta(days=1),
            completed=False,
            user_id=alice_user.id
        ),
        Todo(
            title="Workout session",
            description="Leg day and stretching",
            notes="Track progress and warm up properly.",
            priority="medium",
            due_date=datetime.utcnow() + timedelta(days=3),
            completed=True,
            user_id=alice_user.id
        ),
    ]

    db.session.add_all(todos)
    db.session.commit()

    print("Database seeded successfully.")
    print("Demo user: demo@example.com / password123")
    print("Alice user: alice@example.com / alice123")