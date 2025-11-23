from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app, cors_allowed_origins="*")

players = {}  # player_id -> {name, avatar, score, role}

current_round = {}

@app.route("/")
def index():
    return render_template("index.html"), 200

@socketio.on("join")
def handle_join(data):
    """
    Handles a new player joining the game. Receives player id, name, and avatar from the client.
    Stores the player in memory with a default role, and broadcasts the updated player list to
    all connected clients.
    """
    player_id = data.get("id")
    name = data.get("name")
    avatar = data.get("avatar")
    if not name or not avatar:
        return
    
    # Store player in memory
    players[player_id] = {
        "name": name,
        "avatar": avatar,
        "score": 0,
        "role": "guesser"
    }
    
    # Broadcast updated player list to all clients
    emit("playerList", list(players.values()), broadcast=True)
    print(f"{name} joined! Total players: {len(players)}")

@socketio.on("disconnect")
def handle_disconnect():
    """
    Handles a player disconnecting from the game. Removes the player from memory
    and broadcasts the updated player list to all connected clients.
    """
    player_id = request.sid
    if player_id in players:
        name = players[player_id]["name"]
        del players[player_id]
        emit("playerList", list(players.values()), broadcast=True)
        print(f"{name} disconnected. Total players: {len(players)}")

@socketio.on("startPath")
def handle_start_path(data):
    emit("startPath", data, broadcast=True, include_self=False)

@socketio.on("draw")
def handle_draw(data):
    emit("draw", data, broadcast=True, include_self=False)

@socketio.on("endPath")
def handle_end_path():
    emit("endPath", {}, broadcast=True, include_self=False)

@socketio.on("fill")
def handle_fill(data):
    emit("fill", data, broadcast=True, include_self=False)

@socketio.on("undo")
def handle_undo():
    emit("undo", {}, broadcast=True, include_self=False)

@socketio.on("clear")
def handle_clear():
    emit("clear", {}, broadcast=True, include_self=False)

@app.errorhandler(404)
def error_404(error):
    return render_template("404.html"), 404

@app.errorhandler(403)
def error_403(error):
    return render_template("403.html"), 403

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
