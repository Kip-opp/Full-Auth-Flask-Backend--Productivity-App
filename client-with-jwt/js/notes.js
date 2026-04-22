/**
 * Handles notes CRUD operations and display
 */

const notesModule = (() => {
    let currentPage = 1;
    let currentStatus = null;
    let allNotes = [];
    let totalPages = 1;

    const loadPage = async (page) => {
        const pageContent = document.getElementById('page-content');
        
        if (page === 'notes') {
            currentStatus = null;
            currentPage = 1;
            await loadNotes();
        } else if (page === 'archived') {
            currentStatus = 'archived';
            currentPage = 1;
            await loadNotes();
        }
    };

    const loadNotes = async () => {
        try {
            const response = await api.getNotes(currentPage, 10, currentStatus);
            allNotes = response.data.items;
            totalPages = response.data.pages;
            renderNotes();
        } catch (error) {
            showError('Failed to load notes');
        }
    };

    const renderNotes = () => {
        const pageContent = document.getElementById('page-content');
        
        let html = `
            <div class="flex-between mb-2">
                <h2 class="topbar-title">${currentStatus === 'archived' ? 'Archived Notes' : 'My Notes'}</h2>
                <button class="btn btn-primary" onclick="notesModule.showCreateModal()">+ New Note</button>
            </div>
        `;

        if (allNotes.length === 0) {
            html += `
                <div class="empty-state">
                    <div class="empty-state-icon">📭</div>
                    <h3 class="empty-state-title">No notes yet</h3>
                    <p class="empty-state-text">Create your first note to get started</p>
                    <button class="btn btn-primary" onclick="notesModule.showCreateModal()">Create Note</button>
                </div>
            `;
        } else {
            html += '<div class="grid">';
            allNotes.forEach(note => {
                const date = new Date(note.created_at).toLocaleDateString();
                html += `
                    <div class="note-card">
                        <div class="note-card-header">
                            <h3 class="note-card-title">${escapeHtml(note.title)}</h3>
                            <span class="note-card-status ${note.status}">${note.status}</span>
                        </div>
                        <p class="note-card-content">${escapeHtml(note.content)}</p>
                        <div class="note-card-footer">
                            <span>${date}</span>
                            <div class="note-card-actions">
                                <button class="btn btn-secondary" onclick="notesModule.showEditModal(${note.id})">Edit</button>
                                <button class="btn btn-danger" onclick="notesModule.deleteNote(${note.id})">Delete</button>
                            </div>
                        </div>
                    </div>
                `;
            });
            html += '</div>';

            if (totalPages > 1) {
                html += `
                    <div class="pagination">
                        <button class="btn btn-secondary" onclick="notesModule.previousPage()" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>
                        <span class="pagination-info">Page ${currentPage} of ${totalPages}</span>
                        <button class="btn btn-secondary" onclick="notesModule.nextPage()" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>
                    </div>
                `;
            }
        }

        pageContent.innerHTML = html;
    };

    const showCreateModal = () => {
        showNoteModal(null);
    };

    const showEditModal = async (id) => {
        try {
            const response = await api.getNote(id);
            showNoteModal(response.data);
        } catch (error) {
            showError('Failed to load note');
        }
    };

    const showNoteModal = (note) => {
        const pageContent = document.getElementById('page-content');
        const isEdit = note !== null;

        const modal = document.createElement('div');
        modal.className = 'modal open';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2 class="modal-title">${isEdit ? 'Edit Note' : 'Create Note'}</h2>
                    <button class="modal-close" onclick="this.closest('.modal').remove()">×</button>
                </div>
                <div class="modal-body">
                    <form id="note-form">
                        <div class="form-group">
                            <label for="note-title">Title</label>
                            <input type="text" id="note-title" required maxlength="255" value="${isEdit ? escapeHtml(note.title) : ''}">
                        </div>
                        <div class="form-group">
                            <label for="note-content">Content</label>
                            <textarea id="note-content" required>${isEdit ? escapeHtml(note.content) : ''}</textarea>
                        </div>
                        <div class="form-group">
                            <label for="note-status">Status</label>
                            <select id="note-status">
                                <option value="active" ${isEdit && note.status === 'active' ? 'selected' : ''}>Active</option>
                                <option value="archived" ${isEdit && note.status === 'archived' ? 'selected' : ''}>Archived</option>
                            </select>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
                    <button class="btn btn-primary" onclick="notesModule.saveNote(${isEdit ? note.id : 'null'})">
                        ${isEdit ? 'Update' : 'Create'}
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
    };

    const saveNote = async (id) => {
        const title = document.getElementById('note-title').value;
        const content = document.getElementById('note-content').value;
        const status = document.getElementById('note-status').value;

        if (!title.trim() || !content.trim()) {
            showError('Title and content are required');
            return;
        }

        try {
            if (id) {
                await api.updateNote(id, title, content, status);
                showSuccess('Note updated successfully');
            } else {
                await api.createNote(title, content, status);
                showSuccess('Note created successfully');
            }

            document.querySelector('.modal').remove();
            await loadNotes();
        } catch (error) {
            showError(error.message);
        }
    };

    const deleteNote = async (id) => {
        if (confirm('Are you sure you want to delete this note?')) {
            try {
                await api.deleteNote(id);
                showSuccess('Note deleted successfully');
                await loadNotes();
            } catch (error) {
                showError('Failed to delete note');
            }
        }
    };

    const nextPage = async () => {
        if (currentPage < totalPages) {
            currentPage++;
            await loadNotes();
        }
    };

    const previousPage = async () => {
        if (currentPage > 1) {
            currentPage--;
            await loadNotes();
        }
    };

    return {
        loadPage,
        loadNotes,
        showCreateModal,
        showEditModal,
        saveNote,
        deleteNote,
        nextPage,
        previousPage,
    };
})();

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showError(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-error';
    alert.textContent = message;
    document.body.insertBefore(alert, document.body.firstChild);
    setTimeout(() => alert.remove(), 5000);
}

function showSuccess(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-success';
    alert.textContent = message;
    document.body.insertBefore(alert, document.body.firstChild);
    setTimeout(() => alert.remove(), 5000);
}