import { useState, useEffect } from 'react';
import { notesAPI } from '../services/api';
import NoteForm from './NoteForm';

export default function NotesList() {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState(null);
  const [totalPages, setTotalPages] = useState(1);
  const [showForm, setShowForm] = useState(false);
  const [editingNote, setEditingNote] = useState(null);

  useEffect(() => {
    fetchNotes();
  }, [page, status]);

  const fetchNotes = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await notesAPI.list(page, 10, status);
      setNotes(response.data.data.items);
      setTotalPages(response.data.data.pages);
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to fetch notes');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNote = async (data) => {
    try {
      await notesAPI.create(data.title, data.content, data.status);
      setShowForm(false);
      fetchNotes();
    } catch (err) {
      throw err;
    }
  };

  const handleUpdateNote = async (data) => {
    try {
      await notesAPI.update(editingNote.id, data.title, data.content, data.status);
      setEditingNote(null);
      setShowForm(false);
      fetchNotes();
    } catch (err) {
      throw err;
    }
  };

  const handleDeleteNote = async (id) => {
    if (confirm('Are you sure you want to delete this note?')) {
      try {
        await notesAPI.delete(id);
        fetchNotes();
      } catch (err) {
        setError(err.response?.data?.error?.message || 'Failed to delete note');
      }
    }
  };

  const handleEditNote = (note) => {
    setEditingNote(note);
    setShowForm(true);
  };

  return (
    <div className="container">
      <div className="flex justify-between items-center mb-2">
        <h1>My Notes</h1>
        <button
          className="btn-primary"
          onClick={() => {
            setEditingNote(null);
            setShowForm(!showForm);
          }}
        >
          {showForm ? 'Cancel' : '+ New Note'}
        </button>
      </div>

      {showForm && (
        <NoteForm
          onSubmit={editingNote ? handleUpdateNote : handleCreateNote}
          onCancel={() => {
            setShowForm(false);
            setEditingNote(null);
          }}
          initialNote={editingNote}
        />
      )}

      <div className="card">
        <div className="flex gap-2 mb-2">
          <select
            value={status || ''}
            onChange={(e) => {
              setStatus(e.target.value || null);
              setPage(1);
            }}
            style={{ padding: '10px 12px', borderRadius: '6px', border: '1px solid #ddd' }}
          >
            <option value="">All Notes</option>
            <option value="active">Active</option>
            <option value="archived">Archived</option>
          </select>
        </div>

        {error && <div className="error">{error}</div>}

        {loading ? (
          <div className="text-center">
            <div className="loading"></div>
          </div>
        ) : notes.length === 0 ? (
          <p className="text-center text-muted">No notes yet. Create your first note!</p>
        ) : (
          <>
            <div className="grid">
              {notes.map((note) => (
                <div key={note.id} className="card" style={{ background: '#f9f9f9' }}>
                  <div className="flex justify-between items-center">
                    <div style={{ flex: 1 }}>
                      <h3>{note.title}</h3>
                      <p className="text-muted text-sm" style={{ marginTop: '4px' }}>
                        {new Date(note.createdAt).toLocaleDateString()} • {note.status}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        className="btn-secondary"
                        onClick={() => handleEditNote(note)}
                        style={{ padding: '6px 12px', fontSize: '12px' }}
                      >
                        Edit
                      </button>
                      <button
                        className="btn-danger"
                        onClick={() => handleDeleteNote(note.id)}
                        style={{ padding: '6px 12px', fontSize: '12px' }}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                  <p className="text-muted" style={{ marginTop: '8px', lineHeight: '1.5' }}>
                    {note.content.substring(0, 100)}...
                  </p>
                </div>
              ))}
            </div>

            {totalPages > 1 && (
              <div className="flex justify-between items-center" style={{ marginTop: '20px' }}>
                <button
                  className="btn-secondary"
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1}
                >
                  Previous
                </button>
                <span className="text-muted">
                  Page {page} of {totalPages}
                </span>
                <button
                  className="btn-secondary"
                  onClick={() => setPage(Math.min(totalPages, page + 1))}
                  disabled={page === totalPages}
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}