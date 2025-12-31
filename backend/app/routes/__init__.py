"""API routes for the GitHub Documentation Generator."""

from .analysis import router as analysis_router

__all__ = ['analysis_router']