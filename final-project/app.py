from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
import time

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app, cors_allowed_origins="*")

# SID → playerInfo
players = {}

# Maintain strict join order for sequential drawer rotation
players_order = []
current_drawer_index = 0

current_round = {
    "drawer": None,
    "prompt": None,
    "active": False,
    "correct_guessers": set(),
    "time_started": None
}

words = [
    "dog", "cat", "pizza", "house", "car", "tree", "flower", "airplane",
    "apple", "computer", "star", "sword"
]

def reset_lobby():
    global current_drawer_index

    current_round["drawer"] = None
    current_round["prompt"] = None
    current_round["active"] = False
    current_round["correct_guessers"] = set()
    current_round["time_started"] = None

    current_drawer_index = 0

    # Clear canvas for all players
    emit("clear", {}, broadcast=True)

    # NEW: Tell clients to stop timer & reset header
    emit("lobbyReset", {}, broadcast=True)

def start_new_round():
    global current_drawer_index

    if not players_order:
        print("No players available to start round.")
        return

    # Safety wrap
    if current_drawer_index >= len(players_order):
        current_drawer_index = 0

    drawer_sid = players_order[current_drawer_index]
    prompt = random.choice(words)

    current_round["drawer"] = drawer_sid
    current_round["prompt"] = prompt
    current_round["active"] = True
    current_round["correct_guessers"] = set()
    current_round["time_started"] = time.time()

    print(f"New round started!")
    print(f"Drawer: {players[drawer_sid]['name']}  Prompt: {prompt}")

    emit("clear", {}, broadcast=True)

    for sid in players:
        emit("roundStarted", {
            "role": "drawer" if sid == drawer_sid else "guesser"
        }, room=sid)

    # Drawer
    emit("roundPrompt", {
        "role": "drawer",
        "prompt": prompt
    }, room=drawer_sid)

    # Guesser
    for sid in players:
        if sid != drawer_sid:
            emit("roundPrompt", {
                "role": "guesser",
                "length": len(prompt)
            }, room=sid)

@app.route("/")
def index():
    return render_template("index.html"), 200

@socketio.on("join")
def handle_join(data):
    global current_drawer_index

    sid = request.sid
    name = data.get("name")
    avatar = data.get("avatar")
    client_id = data.get("id")

    if not name or not avatar:
        return

    players[sid] = {
        "client_id": client_id,
        "name": name,
        "avatar": avatar,
        "score": 0
    }

    players_order.append(sid)

    print(f"{name} joined with SID {sid}")
    print("Current players order:", players_order)

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # NEW BLOCK: sync late joiner with active round
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    if current_round["active"]:
        ROUND_TIME = 20

        elapsed = int(time.time() - current_round["time_started"])
        remaining = max(0, ROUND_TIME - elapsed)

        drawer_sid = current_round["drawer"]
        prompt = current_round["prompt"]

        emit("roundStarted", {
            "role": "drawer" if sid == drawer_sid else "guesser",
            "remaining": remaining
        }, room=sid)

        if sid == drawer_sid:
            emit("roundPrompt", {
                "role": "drawer",
                "prompt": prompt
            }, room=sid)
        else:
            emit("roundPrompt", {
                "role": "guesser",
                "length": len(prompt)
            }, room=sid)

        emit("playerList", [
            {
                "name": p["name"],
                "avatar": p["avatar"],
                "score": p["score"]
            }
            for p in players.values()
        ], broadcast=True)

        return
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    # First player
    if len(players_order) == 1:
        emit("waitingForPlayers", {
            "message": "Waiting for one more person..."
        }, room=sid)
        return

    # Second player → start the first round
    if len(players_order) == 2:
        current_drawer_index = 0
        start_new_round()

    emit("playerList", [
        {
            "name": p["name"],
            "avatar": p["avatar"],
            "score": p["score"]
        }
        for p in players.values()
    ], broadcast=True)

@socketio.on("disconnect")
def handle_disconnect():
    global current_drawer_index

    sid = request.sid

    if sid in players:
        name = players[sid]["name"]

        # Remove from players & ordering
        if sid in players_order:
            idx = players_order.index(sid)
            players_order.remove(sid)

            # Adjust drawer index if necessary
            if idx < current_drawer_index:
                current_drawer_index -= 1
            if current_drawer_index >= len(players_order) and players_order:
                current_drawer_index = 0

        del players[sid]

        print(f"{name} left. Remaining players: {len(players)}")

        # BROADCAST SYSTEM MESSAGE
        emit("chatMessage", {
            "name": "",
            "message": f"{name} left the game.",
            "sender_zone": 2,
            "system": True
        }, broadcast=True)

        # Update player list
        emit("playerList", [
            {
                "name": p["name"],
                "avatar": p["avatar"],
                "score": p["score"]
            }
            for p in players.values()
        ], broadcast=True)

        # >>> IMPORTANT: LOBBY RESET LOGIC <<<
        if len(players_order) == 1:
            reset_lobby()

            remaining_sid = players_order[0]
            emit("waitingForPlayers", {
                "message": "Waiting for one more person..."
            }, room=remaining_sid)

            return


@socketio.on("startPath")
def handle_start_path(data):
    if request.sid == current_round["drawer"]:
        emit("startPath", data, broadcast=True, include_self=False)

@socketio.on("draw")
def handle_draw(data):
    if request.sid == current_round["drawer"]:
        emit("draw", data, broadcast=True, include_self=False)

@socketio.on("endPath")
def handle_end_path():
    if request.sid == current_round["drawer"]:
        emit("endPath", {}, broadcast=True, include_self=False)

@socketio.on("fill")
def handle_fill(data):
    if request.sid == current_round["drawer"]:
        emit("fill", data, broadcast=True, include_self=False)

@socketio.on("undo")
def handle_undo():
    if request.sid == current_round["drawer"]:
        emit("undo", {}, broadcast=True, include_self=False)

@socketio.on("clear")
def handle_clear():
    if request.sid == current_round["drawer"]:
        emit("clear", {}, broadcast=True, include_self=False)

@socketio.on("forceRoundEnd")
def handle_force_round_end():
    global current_drawer_index

    if not current_round["active"]:
        return

    current_round["active"] = False
    current_drawer_index = (current_drawer_index + 1) % len(players_order)
    start_new_round()

@socketio.on("chatMessage")
def handle_chat_message(data):
    global current_drawer_index

    sid = request.sid
    if sid not in players:
        return

    message = data.get("message", "").strip()
    name = players[sid]["name"]

    drawer_sid = current_round["drawer"]
    prompt = current_round["prompt"].lower()

    # ------------------------------------------
    # STEP 1 — HANDLE CORRECT GUESS FIRST
    # ------------------------------------------
    if current_round["active"]:
        if sid != drawer_sid and message.lower() == prompt:

            # Already guessed before? Ignore
            if sid not in current_round["correct_guessers"]:
                current_round["correct_guessers"].add(sid)
                players[sid]["score"] += 1

                emit("correctGuess", {
                    "name": name,
                    "score": players[sid]["score"]
                }, broadcast=True)

                # Check if all guessers are done
                guesser_count = len(players_order) - 1
                if len(current_round["correct_guessers"]) == guesser_count:
                    current_round["active"] = False
                    current_drawer_index = (current_drawer_index + 1) % len(players_order)
                    start_new_round()

            # IMPORTANT: Do NOT send the correct-guess message to Zone 1
            return

    # ------------------------------------------
    # STEP 2 — ROUTE MESSAGE BASED ON UPDATED ZONES
    # ------------------------------------------
    # Determine sender zone
    sender_is_drawer = (sid == drawer_sid)
    sender_has_guessed = (sid in current_round["correct_guessers"])

    sender_zone = 2 if (sender_is_drawer or sender_has_guessed) else 1

    # ZONE 1: only unguessed guessers receive zone1 messages
    if sender_zone == 1:
        for sid2 in players:
            if sid2 != drawer_sid and sid2 not in current_round["correct_guessers"]:
                emit("chatMessage", {
                    "name": name,
                    "message": message,
                    "sender_zone": 1
                }, room=sid2)

    # ZONE 2: drawer + guessed guessers receive ALL messages
    for sid2 in players:
        if sid2 == drawer_sid or sid2 in current_round["correct_guessers"]:
            emit("chatMessage", {
                "name": name,
                "message": message,
                "sender_zone": sender_zone
            }, room=sid2)



@app.errorhandler(404)
def error_404(error):
    return render_template("404.html"), 404

@app.errorhandler(403)
def error_403(error):
    return render_template("403.html"), 403

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
