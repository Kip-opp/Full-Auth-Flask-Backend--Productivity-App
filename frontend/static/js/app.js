const messageBox = document.getElementById("message-box");
const authShell = document.getElementById("auth-shell");
const dashboardShell = document.getElementById("dashboard-shell");
const currentUserText = document.getElementById("current-user");
const todoList = document.getElementById("todo-list");
const aiResponse = document.getElementById("ai-response");

const loginForm = document.getElementById("login-form");
const signupForm = document.getElementById("signup-form");
const showLoginBtn = document.getElementById("show-login");
const showSignupBtn = document.getElementById("show-signup");

const todoForm = document.getElementById("todo-form");
const editTodoIdInput = document.getElementById("edit-todo-id");
const todoFormTitle = document.getElementById("todo-form-title");
const todoSubmitBtn = document.getElementById("todo-submit-btn");
const cancelEditBtn = document.getElementById("cancel-edit-btn");

const statTotal = document.getElementById("stat-total");
const statPending = document.getElementById("stat-pending");
const statCompleted = document.getElementById("stat-completed");
const statHigh = document.getElementById("stat-high");

function setMessage(message) {
  messageBox.textContent =
    typeof message === "string" ? message : JSON.stringify(message, null, 2);
}

function getToken() {
  return localStorage.getItem("token");
}

function setToken(token) {
  localStorage.setItem("token", token);
}

function clearToken() {
  localStorage.removeItem("token");
}

function authHeaders() {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${getToken()}`
  };
}

function showLoginView() {
  loginForm.classList.remove("hidden");
  signupForm.classList.add("hidden");
  showLoginBtn.classList.add("active");
  showSignupBtn.classList.remove("active");
}

function showSignupView() {
  signupForm.classList.remove("hidden");
  loginForm.classList.add("hidden");
  showSignupBtn.classList.add("active");
  showLoginBtn.classList.remove("active");
}

function showDashboard() {
  authShell.classList.add("hidden");
  dashboardShell.classList.remove("hidden");
}

function showAuth() {
  dashboardShell.classList.add("hidden");
  authShell.classList.remove("hidden");
}

function resetTodoForm() {
  todoForm.reset();
  editTodoIdInput.value = "";
  todoFormTitle.textContent = "Create Todo";
  todoSubmitBtn.textContent = "Add Todo";
  cancelEditBtn.classList.add("hidden");
}

function populateTodoForm(todo) {
  editTodoIdInput.value = todo.id;
  document.getElementById("todo-title").value = todo.title || "";
  document.getElementById("todo-description").value = todo.description || "";
  document.getElementById("todo-notes").value = todo.notes || "";
  document.getElementById("todo-priority").value = todo.priority || "medium";

  if (todo.due_date) {
    const date = new Date(todo.due_date);
    const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
      .toISOString()
      .slice(0, 16);
    document.getElementById("todo-due-date").value = local;
  } else {
    document.getElementById("todo-due-date").value = "";
  }

  todoFormTitle.textContent = "Update Todo";
  todoSubmitBtn.textContent = "Update Todo";
  cancelEditBtn.classList.remove("hidden");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function updateStats(todos) {
  const total = todos.length;
  const completed = todos.filter((todo) => todo.completed).length;
  const pending = total - completed;
  const high = todos.filter((todo) => todo.priority === "high").length;

  statTotal.textContent = total;
  statPending.textContent = pending;
  statCompleted.textContent = completed;
  statHigh.textContent = high;
}

async function handleResponse(res) {
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error || data.message || "Request failed");
  }
  return data;
}

showLoginBtn.addEventListener("click", showLoginView);
showSignupBtn.addEventListener("click", showSignupView);

signupForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const payload = {
    username: document.getElementById("signup-username").value.trim(),
    email: document.getElementById("signup-email").value.trim(),
    password: document.getElementById("signup-password").value.trim()
  };

  try {
    const res = await fetch("/api/auth/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await handleResponse(res);
    setMessage(data.message || "Signup successful. You can now log in.");
    signupForm.reset();
    showLoginView();
  } catch (error) {
    setMessage(error.message);
  }
});

loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const payload = {
    email: document.getElementById("login-email").value.trim(),
    password: document.getElementById("login-password").value.trim()
  };

  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await handleResponse(res);
    setToken(data.access_token);
    loginForm.reset();
    setMessage("Login successful.");

    await loadCurrentUser();
    await loadTodos();
  } catch (error) {
    setMessage(error.message);
  }
});

todoForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const todoId = editTodoIdInput.value.trim();
  const dueInput = document.getElementById("todo-due-date").value;

  const payload = {
    title: document.getElementById("todo-title").value.trim(),
    description: document.getElementById("todo-description").value.trim(),
    notes: document.getElementById("todo-notes").value.trim(),
    priority: document.getElementById("todo-priority").value,
    due_date: dueInput ? new Date(dueInput).toISOString() : null
  };

  try {
    const isEditing = Boolean(todoId);

    const res = await fetch(isEditing ? `/api/todos/${todoId}` : "/api/todos", {
      method: isEditing ? "PATCH" : "POST",
      headers: authHeaders(),
      body: JSON.stringify(payload)
    });

    const data = await handleResponse(res);

    setMessage(
      data.message || (isEditing ? "Todo updated successfully." : "Todo created successfully.")
    );

    resetTodoForm();
    await loadTodos();
  } catch (error) {
    setMessage(error.message);
  }
});

cancelEditBtn.addEventListener("click", resetTodoForm);

document.getElementById("refresh-btn").addEventListener("click", async () => {
  await loadTodos();
});

document.getElementById("logout-btn").addEventListener("click", () => {
  clearToken();
  currentUserText.textContent = "Not logged in";
  todoList.innerHTML = "";
  aiResponse.textContent = "No AI response yet.";
  resetTodoForm();
  setMessage("Logged out.");
  showAuth();
  showLoginView();
});

document.getElementById("ai-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const payload = {
    prompt: document.getElementById("ai-prompt").value.trim()
  };

  try {
    const res = await fetch("/api/todos/ai-help", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(payload)
    });

    const data = await handleResponse(res);
    aiResponse.textContent = data.response || "No response";
    setMessage("AI response received.");
  } catch (error) {
    setMessage(error.message);
  }
});

document.querySelectorAll(".chip-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.getElementById("ai-prompt").value = btn.textContent;
  });
});

async function loadCurrentUser() {
  const token = getToken();

  if (!token) {
    showAuth();
    showLoginView();
    return;
  }

  try {
    const res = await fetch("/api/auth/me", {
      headers: authHeaders()
    });

    const user = await handleResponse(res);
    currentUserText.textContent = `Logged in as ${user.username} (${user.email})`;
    showDashboard();
  } catch (error) {
    clearToken();
    showAuth();
    showLoginView();
    setMessage(error.message);
  }
}

async function loadTodos(page = 1) {
  try {
    const res = await fetch(`/api/todos?page=${page}&per_page=20`, {
      headers: authHeaders()
    });

    const data = await handleResponse(res);
    const todos = data.items || [];
    renderTodos(todos);
    updateStats(todos);
    setMessage("Todos loaded.");
  } catch (error) {
    setMessage(error.message);
  }
}

function renderTodos(todos) {
  todoList.innerHTML = "";

  if (!todos.length) {
    todoList.innerHTML = `<div class="todo-item"><p>No todos yet. Create your first task.</p></div>`;
    updateStats([]);
    return;
  }

  todos.forEach((todo) => {
    const item = document.createElement("div");
    item.className = "todo-item";

    item.innerHTML = `
      <div class="todo-header">
        <h3>${todo.title}</h3>
        <button class="icon-btn edit-btn" type="button" data-id="${todo.id}" aria-label="Edit todo">✎</button>
      </div>
      <div class="todo-meta">
        Priority: ${todo.priority} |
        Completed: ${todo.completed ? "Yes" : "No"} |
        Due: ${todo.due_date ? new Date(todo.due_date).toLocaleString() : "No due date"}
      </div>
      <p><strong>Description:</strong> ${todo.description || "-"}</p>
      <p><strong>Notes:</strong> ${todo.notes || "-"}</p>
      <div class="todo-actions">
        <button data-id="${todo.id}" class="complete-btn" type="button">Complete</button>
        <button data-id="${todo.id}" class="delete-btn" type="button">Delete</button>
      </div>
    `;

    todoList.appendChild(item);
  });

  document.querySelectorAll(".edit-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = Number(btn.dataset.id);
      const selectedTodo = todos.find((todo) => todo.id === id);

      if (!selectedTodo) return;

      populateTodoForm(selectedTodo);
      setMessage(`Editing "${selectedTodo.title}"`);
    });
  });

  document.querySelectorAll(".complete-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.id;

      try {
        const res = await fetch(`/api/todos/${id}`, {
          method: "PATCH",
          headers: authHeaders(),
          body: JSON.stringify({ completed: true })
        });

        await handleResponse(res);
        setMessage("Todo marked complete.");
        await loadTodos();
      } catch (error) {
        setMessage(error.message);
      }
    });
  });

  document.querySelectorAll(".delete-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.id;

      try {
        const res = await fetch(`/api/todos/${id}`, {
          method: "DELETE",
          headers: authHeaders()
        });

        await handleResponse(res);
        setMessage("Todo deleted.");
        await loadTodos();
      } catch (error) {
        setMessage(error.message);
      }
    });
  });
}

window.addEventListener("DOMContentLoaded", async () => {
  showAuth();
  showLoginView();
  resetTodoForm();
  await loadCurrentUser();

  if (getToken()) {
    await loadTodos();
  }
});