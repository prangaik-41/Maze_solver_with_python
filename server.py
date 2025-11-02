# server.py - Optimized Classroom Multiplayer Maze (Flask + Socket.IO)
import os, time, sqlite3, random
from threading import Lock
from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit, join_room
# Use eventlet for better concurrency in classroom LAN
async_mode = 'eventlet'

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = os.environ.get('MAZE_SECRET','change-me')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode=async_mode)
thread_lock = Lock()

DB_PATH = 'leaderboard.db'
MAX_MOVE_RATE_PER_SEC = 10  # prevent clients spamming moves (rate limit)

# in-memory rate limiter: sid -> [last_ts, tokens]
rate_tokens = {}

# basic in-memory games: room -> game_state
games = {}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leaderboard
                 (id INTEGER PRIMARY KEY, player TEXT, room TEXT, time_taken INTEGER, moves INTEGER, score INTEGER, ts INTEGER)''')
    conn.commit()
    conn.close()
init_db()

def generate_maze(size):
    maze = [['#' for _ in range(size)] for _ in range(size)]
    start = (1,1); end = (size-2, size-2)
    stack = [start]; maze[start[0]][start[1]] = '.'
    directions = [(-2,0),(0,2),(2,0),(0,-2)]
    while stack:
        y,x = stack[-1]
        neigh = []
        for dy,dx in directions:
            ny,nx = y+dy, x+dx
            if 1 <= ny < size-1 and 1 <= nx < size-1 and maze[ny][nx] == '#':
                neigh.append((ny,nx,dy//2,dx//2))
        if neigh:
            ny,nx,dy,dx = random.choice(neigh)
            maze[y+dy][x+dx] = '.'
            maze[ny][nx] = '.'
            stack.append((ny,nx))
        else:
            stack.pop()
    maze[start[0]][start[1]] = 'S'
    maze[end[0]][end[1]] = 'E'
    return maze, start, end

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game/<room>')
def game(room):
    return render_template('game.html', room=room)

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

def broadcast_leaderboard(room):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT player, time_taken, moves, score FROM leaderboard WHERE room=? ORDER BY score DESC, time_taken ASC LIMIT 50", (room,))
    rows = c.fetchall()
    conn.close()
    lb = [{'player': r[0], 'time': r[1], 'moves': r[2], 'score': r[3]} for r in rows]
    socketio.emit('leaderboard', {'room': room, 'leaderboard': lb}, room=room)

def add_leaderboard(room, player, time_taken, moves, score):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO leaderboard (player, room, time_taken, moves, score, ts) VALUES (?, ?, ?, ?, ?, ?)",
              (player, room, time_taken, moves, score, int(time.time())))
    conn.commit()
    conn.close()

def allow_move(sid):
    # simple token bucket per-sid
    now = time.time()
    bucket = rate_tokens.get(sid, [now, MAX_MOVE_RATE_PER_SEC])
    last, tokens = bucket
    elapsed = now - last
    # refill
    tokens = min(MAX_MOVE_RATE_PER_SEC, tokens + elapsed * MAX_MOVE_RATE_PER_SEC)
    if tokens >= 1:
        tokens -= 1
        rate_tokens[sid] = [now, tokens]
        return True
    rate_tokens[sid] = [now, tokens]
    return False

@socketio.on('join')
def on_join(data):
    room = data.get('room','classroom')
    name = data.get('name') or 'Player'
    size = int(data.get('size') or 15)
    color = data.get('color') or '#0066FF'
    sid = request.sid
    join_room(room)
    if room not in games:
        maze, start, end = generate_maze(size)
        games[room] = {'maze': maze, 'size': size, 'start': start, 'end': end, 'players': {}}
    gs = games[room]
    gs['players'][sid] = {'name': name, 'pos': list(gs['start']), 'moves': 0, 'start_time': int(time.time()), 'finished': False, 'color': color}
    # send current state to room (lightweight)
    socketio.emit('game_state', {'maze': gs['maze'], 'players': {k: {'name':v['name'], 'pos':v['pos'], 'moves':v['moves'], 'color':v['color']} for k,v in gs['players'].items()}, 'size': gs['size']}, room=room)

@socketio.on('move')
def on_move(data):
    room = data.get('room')
    if not room or room not in games: return
    sid = request.sid
    if sid not in games[room]['players']: return
    if not allow_move(sid):
        return  # drop excessive moves
    dy = int(data.get('dy',0)); dx = int(data.get('dx',0))
    gs = games[room]
    py, px = gs['players'][sid]['pos']
    ny, nx = py+dy, px+dx
    if 0 <= ny < gs['size'] and 0 <= nx < gs['size'] and gs['maze'][ny][nx] != '#':
        gs['players'][sid]['pos'] = [ny, nx]
        gs['players'][sid]['moves'] += 1
        socketio.emit('player_moved', {'sid': sid, 'pos': gs['players'][sid]['pos'], 'moves': gs['players'][sid]['moves']}, room=room)
        # finish check
        if [ny,nx] == list(gs['end']) and not gs['players'][sid]['finished']:
            gs['players'][sid]['finished'] = True
            time_taken = int(time.time()) - gs['players'][sid]['start_time']
            moves = gs['players'][sid]['moves']
            score = max(0, 1000 - (moves * 10) - (time_taken * 2))
            add_leaderboard(room, gs['players'][sid]['name'], time_taken, moves, score)
            socketio.emit('player_finished', {'sid': sid, 'name': gs['players'][sid]['name'], 'time': time_taken, 'moves': moves, 'score': score}, room=room)
            broadcast_leaderboard(room)

@socketio.on('get_leaderboard')
def on_get_leaderboard(data):
    room = data.get('room')
    if not room: return
    broadcast_leaderboard(room)

@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    for room, gs in list(games.items()):
        if sid in gs['players']:
            del gs['players'][sid]
            socketio.emit('player_left', {'sid': sid}, room=room)

if __name__ == '__main__':
    # Run: python server.py
    # Use eventlet for scalable connections: pip install eventlet
    print("Starting Maze server on 0.0.0.0:5000")
    socketio.run(app, host='0.0.0.0', port=5000)