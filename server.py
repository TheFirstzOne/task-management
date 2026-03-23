# -*- coding: utf-8 -*-
"""FastAPI server entry point — Phase 21"""
import uvicorn

if __name__ == "__main__":
    from app.database import init_db
    init_db()
    from server.main import app
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
