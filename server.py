#!/usr/bin/env python3
"""
Simple server launcher for the trading bot dashboard
"""

import uvicorn
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Import the app from the dashboard module
    from src.dashboard.main import app

    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True, reload_dirs=["src"])
