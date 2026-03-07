import uvicorn
from backend.api_routes import app

if __name__ == "__main__":
    print("[SERVER] Starting Project JD Backend on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
