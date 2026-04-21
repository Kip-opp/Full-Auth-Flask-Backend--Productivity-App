import { useState, useEffect } from 'react';

export default function NoteForm({ onSubmit, onCancel, initialNote = null }) {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [status, setStatus] = useState('active');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (initialNote) {
      setTitle(initialNote.title);
      setContent(initialNote.content);
      setStatus(initialNote.status);
    }
  }, [initialNote]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!title.trim() || !content.trim()) {
      setError('Title and content are required');
      return;
    }

    setLoading(true);
    try {
      await onSubmit({ title, content, status });
      setTitle('');
      setContent('');
      setStatus('active');
    } catch (err) {
      setError(err.response?.data?.error?.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2 className="mb-2">{initialNote ? 'Edit Note' : 'Create New Note'}</h2>

      <form onSubmit={handleSubmit}>
        <div className="mb-2">
          <label>Title</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            maxLength="255"
            style={{ width: '100%', marginTop: '4px' }}
          />
          <div className="text-sm text-muted">{title.length}/255</div>
        </div>

        <div className="mb-2">
          <label>Content</label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows="6"
            style={{ width: '100%', marginTop: '4px' }}
          />
        </div>

        <div className="mb-2">
          <label>Status</label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            style={{ width: '100%', marginTop: '4px', padding: '10px 12px', borderRadius: '6px', border: '1px solid #ddd' }}
          >
            <option value="active">Active</option>
            <option value="archived">Archived</option>
          </select>
        </div>

        {error && <div className="error">{error}</div>}

        <div className="flex gap-2" style={{ marginTop: '16px' }}>
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Saving...' : initialNote ? 'Update Note' : 'Create Note'}
          </button>
          <button type="button" className="btn-secondary" onClick={onCancel}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}