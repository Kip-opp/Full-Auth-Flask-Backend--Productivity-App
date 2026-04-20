from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.todo import Todo

todos_bp = Blueprint("todos", __name__)


@todos_bp.get("")
@jwt_required()
def get_todos():
    user_id = int(get_jwt_identity())

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 5, type=int)
    status = request.args.get("status", type=str)
    scope = request.args.get("scope", type=str)

    if page < 1:
        return jsonify({"error": "page must be greater than or equal to 1"}), 400

    if per_page < 1 or per_page > 100:
        return jsonify({"error": "per_page must be between 1 and 100"}), 400

    query = Todo.query.filter_by(user_id=user_id)

    if status:
        if status not in {"completed", "pending"}:
            return jsonify({"error": "status must be 'completed' or 'pending'"}), 400
        query = query.filter_by(completed=(status == "completed"))

    now = datetime.utcnow()
    if scope:
        if scope not in {"upcoming", "previous"}:
            return jsonify({"error": "scope must be 'upcoming' or 'previous'"}), 400
        if scope == "upcoming":
            query = query.filter(Todo.due_date.isnot(None), Todo.due_date >= now)
        else:
            query = query.filter(Todo.due_date.isnot(None), Todo.due_date < now)

    pagination = query.order_by(
        Todo.due_date.asc().nullslast(),
        Todo.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "items": [todo.to_dict() for todo in pagination.items],
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev
    }), 200


@todos_bp.post("")
@jwt_required()
def create_todo():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    title = data.get("title", "").strip()
    description = data.get("description")
    notes = data.get("notes")
    priority = data.get("priority", "medium")
    due_date_raw = data.get("due_date")

    if not title:
        return jsonify({"error": "title is required"}), 400

    if priority not in {"low", "medium", "high"}:
        return jsonify({"error": "priority must be low, medium, or high"}), 400

    due_date = None
    if due_date_raw not in [None, ""]:
        try:
            due_date = datetime.fromisoformat(due_date_raw)
        except ValueError:
            return jsonify({"error": "due_date must be a valid ISO datetime string"}), 400

    todo = Todo(
        title=title,
        description=description,
        notes=notes,
        priority=priority,
        due_date=due_date,
        user_id=user_id
    )

    db.session.add(todo)
    db.session.commit()

    return jsonify({
        "message": "Todo created successfully",
        "todo": todo.to_dict()
    }), 201


@todos_bp.get("/<int:todo_id>")
@jwt_required()
def get_todo(todo_id):
    user_id = int(get_jwt_identity())
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()

    if not todo:
        return jsonify({"error": "Todo not found"}), 404

    return jsonify(todo.to_dict()), 200


@todos_bp.patch("/<int:todo_id>")
@jwt_required()
def update_todo(todo_id):
    user_id = int(get_jwt_identity())
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()

    if not todo:
        return jsonify({"error": "Todo not found"}), 404

    data = request.get_json() or {}

    if "title" in data:
        title = str(data["title"]).strip()
        if not title:
            return jsonify({"error": "title cannot be empty"}), 400
        todo.title = title

    if "description" in data:
        todo.description = data["description"]

    if "notes" in data:
        todo.notes = data["notes"]

    if "priority" in data:
        priority = data["priority"]
        if priority not in {"low", "medium", "high"}:
            return jsonify({"error": "priority must be low, medium, or high"}), 400
        todo.priority = priority

    if "completed" in data:
        if not isinstance(data["completed"], bool):
            return jsonify({"error": "completed must be a boolean"}), 400
        todo.completed = data["completed"]

    if "due_date" in data:
        due_date_value = data["due_date"]
        if due_date_value in [None, ""]:
            todo.due_date = None
        else:
            try:
                todo.due_date = datetime.fromisoformat(due_date_value)
            except ValueError:
                return jsonify({"error": "due_date must be a valid ISO datetime string"}), 400

    db.session.commit()

    return jsonify({
        "message": "Todo updated successfully",
        "todo": todo.to_dict()
    }), 200


@todos_bp.delete("/<int:todo_id>")
@jwt_required()
def delete_todo(todo_id):
    user_id = int(get_jwt_identity())
    todo = Todo.query.filter_by(id=todo_id, user_id=user_id).first()

    if not todo:
        return jsonify({"error": "Todo not found"}), 404

    db.session.delete(todo)
    db.session.commit()

    return jsonify({"message": "Todo deleted successfully"}), 200