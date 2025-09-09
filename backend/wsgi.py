# backend/wsgi.py
from backend.app import create_app, socketio  # <-- absolute import

# WSGI entrypoint (e.g., gunicorn -k eventlet -w 1 backend.wsgi:app)
app = create_app()

if __name__ == "__main__":
    if socketio:
        socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)
    else:
        app.run(host="0.0.0.0", port=5000)
