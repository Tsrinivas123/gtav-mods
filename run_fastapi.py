#!/usr/bin/env python
"""
Run PawanMod FastAPI High-Performance Backend
Usage:
    python run_fastapi.py
    python run_fastapi.py --port 8001 --reload
"""
import sys
import uvicorn
import argparse

def main():
    parser = argparse.ArgumentParser(description="PawanMod FastAPI Backend Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host IP (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8001, help="Port (default: 8001)")
    parser.add_argument("--reload", action="store_true", default=True, help="Enable auto-reload on code change")

    args = parser.parse_args()

    print(f"\n=======================================================")
    print(f"  🚀 Starting PawanMod FastAPI Backend")
    print(f"  📍 Server URL:      http://{args.host}:{args.port}")
    print(f"  📖 Swagger Docs:    http://{args.host}:{args.port}/docs")
    print(f"  📚 ReDoc:           http://{args.host}:{args.port}/redoc")
    print(f"=======================================================\n")

    uvicorn.run("fastapi_app.main:app", host=args.host, port=args.port, reload=args.reload)

if __name__ == "__main__":
    main()

