MULTIPLAYER MAZE - Classroom Package
-----------------------------------
Files included:
  - server.py            : Flask + Socket.IO server (optimized)
  - templates/index.html : Start page (name entry + difficulty)
  - templates/game.html  : Game client (keyboard + touch)
  - static/touch.js      : placeholder for touch code
  - maze_game_qr.png     : QR code pointing to http://192.168.237.182:5000
  - README.txt           : this file

Quick start (on host laptop):
1) Install Python 3.8+
2) Create venv and install deps:
     python -m venv venv
     source venv/bin/activate    # or venv\Scripts\activate on Windows
     pip install -U pip
     pip install flask flask-socketio eventlet qrcode pillow

3) Place these files in a folder and run:
     python server.py

4) Ensure your laptop firewall allows port 5000 inbound on local network.
5) Share the QR (maze_game_qr.png) or the URL:
     http://192.168.237.182:5000
6) Students scan QR -> Enter name -> Start -> Play.
7) Leaderboard updates automatically when players finish.

Notes & optimizations included:
 - Uses eventlet for many concurrent socket connections (good for ~100 clients on LAN)
 - Simple rate-limiter to avoid spammy move events
 - SQLite leaderboard saved to leaderboard.db
 - Both keyboard and on-screen buttons included for mobile use
 - Maze generation server-side; clients only render the grid

If you'd like, I can also:
  - Add a server admin panel (connected players, reset leaderboard, new maze)
  - Bundle this into a single clickable run script for Windows/macOS
  - Add a more advanced on-screen joystick for mobile
