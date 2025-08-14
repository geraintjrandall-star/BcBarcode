from app import create_app, socketio

app = create_app()

if __name__ == "__main__":
    # Get LAN IP
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "127.0.0.1"

    print(f"\nApp running on:")
    print(f"  Local:   http://127.0.0.1:5000")
    print(f"  Network: http://{local_ip}:5000\n")

    # Run Flask with SocketIO
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)