"""
Vercel Python runtime entrypoint.

Deploy the `backend/` directory as a dedicated Vercel project and expose the
FastAPI application through this module.
"""

from main import app

