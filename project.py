"""Legacy entry point — use app.py only (one server at a time)."""

from app import app

if __name__ == "__main__":
    print("Starting via app.py — run: python app.py")
    app.run(debug=True, host="127.0.0.1", port=5000)
