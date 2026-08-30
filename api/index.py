"""Vercel serverless entry point for the Flask backend.

Vercel invokes a Python file that exposes a WSGI-compatible `app`
variable. This module wraps the existing Flask application factory so
the same code that runs locally can run as a serverless function on
Vercel.
"""
import os
import sys

# Allow imports from the backend/ directory.
BACKEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'backend')
BACKEND_DIR = os.path.abspath(BACKEND_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Force a hosted DB on Vercel. The local SQLite path is not writable
# from serverless functions. Set DATABASE_URL (or SQLALCHEMY_DATABASE_URI)
# in the Vercel project settings to point at Postgres before deploying.
if not os.getenv('SQLALCHEMY_DATABASE_URI') and not os.getenv('DATABASE_URL'):
    os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/vercel-fallback.db'

# Required secrets must be supplied via the Vercel project env. These
# fallbacks are intentionally weak so misconfiguration is obvious.
os.environ.setdefault('SECRET_KEY', 'vercel-insecure-dev-secret')
os.environ.setdefault('JWT_SECRET_KEY', 'vercel-insecure-jwt-secret')

from app import create_app  # noqa: E402  (sys.path mutated above)

app = create_app()
