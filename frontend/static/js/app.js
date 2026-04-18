const messageBox = document.getElementById("message-box");
const userSection = document.getElementById("user-section");
const appSection = document.getElementById("app-section");
const aiSection = document.getElementById("ai-section");
const currentUserText = document.getElementById("current-user");
const todoList = document.getElementById("todo-list");
const aiResponse = document.getElementById("ai-response");

function setMessage(message) {
  messageBox.textContent = typeof message === "string" ? message : JSON.stringify(message, null, 2);
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
    "Authorization": `Bearer ${getToken()}`
  };
}

function showApp() {
  userSection.classList.remove("hidden");
  appSection.classList.remove("hidden");
  aiSection.classList.remove("hidden");
}

function hideApp() {
  userSection.classList.add("hidden");
  appSection.classList.add("hidden");
  aiSection.classList.add("hidden");
}

async function handleResponse(res) {
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error || data.message || "Request failed");
  }
  return data;
}

document.getElementById("signup-form").addEventListener("submit", async (e) => {
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
    setMessage(data);
    e.target.reset();
  } catch (error) {
    setMessage(error.message);
  }
});

document.getElementById("login-form").addEventListener("submit", async (e) => {
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
    setMessage(data);
    e.target.reset();

    await loadCurrentUser();
    await loadTodos();
  } catch (error) {
    setMessage(error.message);
  }
});

document.getElementById("todo-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const dueInput = document.getElementById("todo-due-date").value;

  const payload = {
    title: document.getElementById("todo-title").value.trim(),
    description: document.getElementById("todo-description").value.trim(),
    notes: document.getElementById("todo-notes").value.trim(),
    priority: document.getElementById("todo-priority").value,
    due_date: dueInput ? new Date(dueInput).toISOString() : null
  };

  try {
    const res = await fetch("/api/todos", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(payload)
    });

    const data = await handleResponse(res);
    setMessage(data);
    e.target.reset();
    await loadTodos();
  } catch (error) {
    setMessage(error.message);
  }
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

document.getElementById("refresh-btn").addEventListener("click", async () => {
  await loadTodos();
});

document.getElementById("logout-btn").addEventListener("click", () => {
  clearToken();
  hideApp();
  currentUserText.textContent = "Not logged in";
  todoList.innerHTML = "";
  aiResponse.textContent = "";
  setMessage("Logged out.");
});

async function loadCurrentUser() {
  const token = getToken();
  if (!token) {
    hideApp();
    return;
  }

  try {
    const res = await fetch("/api/auth/me", {
      headers: authHeaders()
    });

    const user = await handleResponse(res);
    currentUserText.textContent = `Logged in as ${user.username} (${user.email})`;
    showApp();
  } catch (error) {
    clearToken();
    hideApp();
    setMessage(error.message);
  }
}

async function loadTodos(page = 1) {
  try {
    const res = await fetch(`/api/todos?page=${page}&per_page=10`, {
      headers: authHeaders()
    });

    const data = await handleResponse(res);
    renderTodos(data.items || []);
    setMessage(data);
  } catch (error) {
    setMessage(error.message);
  }
}

function renderTodos(todos) {
  todoList.innerHTML = "";

  if (!todos.length) {
    todoList.innerHTML = "<p>No todos yet.</p>";
    return;
  }

  todos.forEach((todo) => {
    const item = document.createElement("div");
    item.className = "todo-item";

    item.innerHTML = `
      <h3>${todo.title}</h3>
      <div class="todo-meta">
        Priority: ${todo.priority} |
        Completed: ${todo.completed ? "Yes" : "No"} |
        Due: ${todo.due_date ? new Date(todo.due_date).toLocaleString() : "No due date"}
      </div>
      <p><strong>Description:</strong> ${todo.description || "-"}</p>
      <p><strong>Notes:</strong> ${todo.notes || "-"}</p>
      <div class="todo-actions">
        <button data-id="${todo.id}" class="complete-btn">Complete</button>
        <button data-id="${todo.id}" class="delete-btn">Delete</button>
      </div>
    `;

    todoList.appendChild(item);
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

        const data = await handleResponse(res);
        setMessage(data);
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

        const data = await handleResponse(res);
        setMessage(data);
        await loadTodos();
      } catch (error) {
        setMessage(error.message);
      }
    });
  });
}

window.addEventListener("DOMContentLoaded", async () => {
  await loadCurrentUser();
  if (getToken()) {
    await loadTodos();
  }
});