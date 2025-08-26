# run_dev.py
"""
Development runner with auto-reload enabled
Use this for development: python run_dev.py
"""

import uvicorn

if __name__ == "__main__":
    print("Starting development server with auto-reload...")
    print("Access the API at: http://localhost:8000")
    print("Interactive docs at: http://localhost:8000/docs")
    print("Press Ctrl+C to stop")
    
    uvicorn.run(
        "main:app",  # Import string format for reload
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload
        log_level="info"
    )