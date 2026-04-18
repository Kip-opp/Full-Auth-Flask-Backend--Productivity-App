from datetime import datetime
from getpass import getpass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

from app import create_app
from app.extensions import db, bcrypt
from app.models.user import User
from app.models.todo import Todo
from app.services.ai_service import AIService

app = create_app()
console = Console()


def show_welcome():
    console.clear()
    console.print(
        Panel.fit(
            "[bold cyan]AI TODO CLI[/bold cyan]\n[dim]Manual todo management + Grok help in terminal[/dim]",
            border_style="cyan"
        )
    )


def show_commands():
    table = Table(title="Available Commands", header_style="bold magenta")
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")

    table.add_row("list", "Show all todos")
    table.add_row("upcoming", "Show upcoming todos")
    table.add_row("previous", "Show previous or past-due todos")
    table.add_row("view <id>", "View full details for one todo")
    table.add_row("add", "Add a new todo")
    table.add_row("update", "Update a todo")
    table.add_row("notes", "Add or edit notes on a todo")
    table.add_row("complete", "Mark a todo as complete")
    table.add_row("delete", "Delete a todo")
    table.add_row("ai <prompt>", "Ask Grok for help using your current todos")
    table.add_row("help", "Show command table again")
    table.add_row("quit", "Exit the CLI")

    console.print(table)


def render_todos(todos, title="Todos"):
    if not todos:
        console.print(Panel("No todos found.", border_style="yellow"))
        return

    table = Table(title=title, header_style="bold green")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="white")
    table.add_column("Status", style="magenta")
    table.add_column("Priority", style="yellow")
    table.add_column("Due Date", style="green")

    for todo in todos:
        status = "DONE" if todo.completed else "PENDING"
        due = todo.due_date.strftime("%Y-%m-%d %H:%M") if todo.due_date else "No due date"
        table.add_row(
            str(todo.id),
            todo.title,
            status,
            todo.priority,
            due
        )

    console.print(table)


def get_todos(user, mode="all"):
    now = datetime.utcnow()
    query = Todo.query.filter_by(user_id=user.id)

    if mode == "upcoming":
        query = query.filter(Todo.due_date.isnot(None), Todo.due_date >= now)
    elif mode == "previous":
        query = query.filter(Todo.due_date.isnot(None), Todo.due_date < now)

    return query.order_by(Todo.due_date.asc().nullslast(), Todo.created_at.desc()).all()


def view_todo(user, todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=user.id).first()

    if not todo:
        console.print("[bold red]Todo not found.[/bold red]")
        return

    details = Table(title=f"Todo #{todo.id}", header_style="bold blue")
    details.add_column("Field", style="cyan", no_wrap=True)
    details.add_column("Value", style="white")

    details.add_row("Title", todo.title)
    details.add_row("Description", todo.description or "-")
    details.add_row("Notes", todo.notes or "-")
    details.add_row("Priority", todo.priority)
    details.add_row("Completed", "Yes" if todo.completed else "No")
    details.add_row(
        "Due Date",
        todo.due_date.strftime("%Y-%m-%d %H:%M") if todo.due_date else "No due date"
    )
    details.add_row(
        "Created At",
        todo.created_at.strftime("%Y-%m-%d %H:%M") if todo.created_at else "-"
    )
    details.add_row(
        "Updated At",
        todo.updated_at.strftime("%Y-%m-%d %H:%M") if todo.updated_at else "-"
    )

    console.print(details)


def add_todo(user):
    console.print("\n[bold cyan]Add New Todo[/bold cyan]")
    title = Prompt.ask("Title").strip()
    description = Prompt.ask("Description", default="").strip()
    notes = Prompt.ask("Notes", default="").strip()
    priority = Prompt.ask(
        "Priority",
        choices=["low", "medium", "high"],
        default="medium"
    ).strip()
    due_raw = Prompt.ask("Due date (YYYY-MM-DD HH:MM)", default="").strip()

    if not title:
        console.print("[bold red]Title is required.[/bold red]")
        return

    due_date = None
    if due_raw:
        try:
            due_date = datetime.strptime(due_raw, "%Y-%m-%d %H:%M")
        except ValueError:
            console.print("[bold red]Invalid date format. Use YYYY-MM-DD HH:MM[/bold red]")
            return

    todo = Todo(
        title=title,
        description=description or None,
        notes=notes or None,
        priority=priority,
        due_date=due_date,
        user_id=user.id
    )
    db.session.add(todo)
    db.session.commit()
    console.print("[bold green]Todo added successfully.[/bold green]")


def update_todo(user):
    todo_id = Prompt.ask("Enter todo ID to update").strip()

    if not todo_id.isdigit():
        console.print("[bold red]Invalid ID.[/bold red]")
        return

    todo = Todo.query.filter_by(id=int(todo_id), user_id=user.id).first()
    if not todo:
        console.print("[bold red]Todo not found.[/bold red]")
        return

    console.print("[dim]Leave a field blank to keep the current value.[/dim]")

    current_due = todo.due_date.strftime("%Y-%m-%d %H:%M") if todo.due_date else ""
    new_title = Prompt.ask("Title", default=todo.title).strip()
    new_description = Prompt.ask("Description", default=todo.description or "").strip()
    new_notes = Prompt.ask("Notes", default=todo.notes or "").strip()
    new_priority = Prompt.ask(
        "Priority",
        choices=["low", "medium", "high"],
        default=todo.priority
    ).strip()
    new_completed = Prompt.ask(
        "Completed",
        choices=["yes", "no"],
        default="yes" if todo.completed else "no"
    ).strip()
    new_due_raw = Prompt.ask("Due date (YYYY-MM-DD HH:MM)", default=current_due).strip()

    todo.title = new_title
    todo.description = new_description or None
    todo.notes = new_notes or None
    todo.priority = new_priority
    todo.completed = new_completed == "yes"

    if new_due_raw:
        try:
            todo.due_date = datetime.strptime(new_due_raw, "%Y-%m-%d %H:%M")
        except ValueError:
            console.print("[bold red]Invalid date format. Use YYYY-MM-DD HH:MM[/bold red]")
            return
    else:
        todo.due_date = None

    db.session.commit()
    console.print("[bold green]Todo updated successfully.[/bold green]")


def edit_notes(user):
    todo_id = Prompt.ask("Enter todo ID for notes").strip()

    if not todo_id.isdigit():
        console.print("[bold red]Invalid ID.[/bold red]")
        return

    todo = Todo.query.filter_by(id=int(todo_id), user_id=user.id).first()
    if not todo:
        console.print("[bold red]Todo not found.[/bold red]")
        return

    console.print(f"\n[bold cyan]Current notes:[/bold cyan] {todo.notes or '-'}")
    new_notes = Prompt.ask("New notes", default=todo.notes or "").strip()

    todo.notes = new_notes or None
    db.session.commit()

    console.print("[bold green]Notes updated successfully.[/bold green]")


def complete_todo(user):
    todo_id = Prompt.ask("Enter todo ID to mark complete").strip()

    if not todo_id.isdigit():
        console.print("[bold red]Invalid ID.[/bold red]")
        return

    todo = Todo.query.filter_by(id=int(todo_id), user_id=user.id).first()
    if not todo:
        console.print("[bold red]Todo not found.[/bold red]")
        return

    todo.completed = True
    db.session.commit()
    console.print("[bold green]Todo marked as complete.[/bold green]")


def delete_todo(user):
    todo_id = Prompt.ask("Enter todo ID to delete").strip()

    if not todo_id.isdigit():
        console.print("[bold red]Invalid ID.[/bold red]")
        return

    todo = Todo.query.filter_by(id=int(todo_id), user_id=user.id).first()
    if not todo:
        console.print("[bold red]Todo not found.[/bold red]")
        return

    db.session.delete(todo)
    db.session.commit()
    console.print("[bold green]Todo deleted successfully.[/bold green]")


def ai_help(user, prompt):
    todos = Todo.query.filter_by(user_id=user.id).order_by(Todo.created_at.desc()).all()
    service = AIService(app)
    result = service.ask_grok(prompt, todos)

    if result["success"]:
        console.print(Panel(result["response"], title="Grok", border_style="blue"))
    else:
        console.print(Panel(result["response"], title="Error", border_style="red"))


def register_user():
    console.print("\n[bold cyan]Register[/bold cyan]")
    username = Prompt.ask("Username").strip()
    email = Prompt.ask("Email").strip().lower()
    password = getpass("Password: ").strip()

    if not username or not email or not password:
        console.print("[bold red]All fields are required.[/bold red]")
        return None

    existing_user = User.query.filter(
        (User.email == email) | (User.username == username)
    ).first()

    if existing_user:
        console.print("[bold red]User with that email or username already exists.[/bold red]")
        return None

    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User(username=username, email=email, password_hash=password_hash)

    db.session.add(user)
    db.session.commit()

    console.print("[bold green]Registration successful. You can now log in.[/bold green]")
    return user


def login_user():
    while True:
        show_welcome()
        console.print("[bold white]Login to continue[/bold white]")
        console.print("[dim]Type 'register' as email to create a new account, or 'quit' to exit.[/dim]\n")

        email = Prompt.ask("Email").strip().lower()

        if email == "quit":
            return None

        if email == "register":
            register_user()
            continue

        password = getpass("Password: ").strip()

        user = User.query.filter_by(email=email).first()
        if not user:
            console.print("[bold red]User not found.[/bold red]")
            continue

        if not bcrypt.check_password_hash(user.password_hash, password):
            console.print("[bold red]Invalid password.[/bold red]")
            continue

        console.print(f"[bold green]Welcome, {user.username}![/bold green]\n")
        return user


def main():
    with app.app_context():
        user = login_user()
        if not user:
            console.print("[bold yellow]Goodbye.[/bold yellow]")
            return

        show_commands()

        while True:
            command = Prompt.ask("\n[bold cyan]todo[/bold cyan]").strip()

            if command == "list":
                render_todos(get_todos(user, "all"), "All Todos")
            elif command == "upcoming":
                render_todos(get_todos(user, "upcoming"), "Upcoming Todos")
            elif command == "previous":
                render_todos(get_todos(user, "previous"), "Previous / Past-due Todos")
            elif command.startswith("view "):
                raw_id = command.split(" ", 1)[1].strip()
                if raw_id.isdigit():
                    view_todo(user, int(raw_id))
                else:
                    console.print("[bold red]Usage: view <id>[/bold red]")
            elif command == "add":
                add_todo(user)
            elif command == "update":
                update_todo(user)
            elif command == "notes":
                edit_notes(user)
            elif command == "complete":
                complete_todo(user)
            elif command == "delete":
                delete_todo(user)
            elif command.startswith("ai "):
                prompt = command[3:].strip()
                if not prompt:
                    console.print("[bold red]Please provide a prompt after 'ai'.[/bold red]")
                else:
                    ai_help(user, prompt)
            elif command == "help":
                show_commands()
            elif command in {"quit", "exit"}:
                console.print("[bold yellow]Goodbye.[/bold yellow]")
                break
            else:
                console.print("[bold red]Unknown command.[/bold red]")
                show_commands()


if __name__ == "__main__":
    main()