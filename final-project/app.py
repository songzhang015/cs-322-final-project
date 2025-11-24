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

canvas_history = []

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

    print("Round initializing...")
    print(f"Drawer: {players[drawer_sid]['name']}  Prompt: {prompt}")

    canvas_history.clear()
    # Immediate UI clear
    emit("clear", {}, broadcast=True)

    # PHASE 1 — Tell clients the round is starting (NO timer, NO tools)
    emit("roundStarting", {}, broadcast=True)

    # Delay 3 seconds
    socketio.sleep(3)

    current_round["time_started"] = time.time()

    # PHASE 2 — Now actually start round with timestamp
    for sid in players:
        emit("roundStarted", {
            "role": "drawer" if sid == drawer_sid else "guesser",
            "startTime": current_round["time_started"]  # <-- ADDED
        }, room=sid)

    # Drawer prompt
    emit("roundPrompt", {
        "role": "drawer",
        "prompt": prompt
    }, room=drawer_sid)

    # Guessers get length
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
            "startTime": current_round["time_started"]  # <-- ADD THIS INSTEAD
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
        for event_type, payload in canvas_history:
            emit(event_type, payload, room=sid)

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
            "type": "leave",
            "message": f"{name} left the game.",
            "sender_zone": 2
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
            if current_round["active"] and current_round["prompt"]:
                emit("chatMessage", {
                    "type": "reveal",
                    "word": current_round["prompt"],
                    "sender_zone": 2
                }, broadcast=True)
            reset_lobby()

            remaining_sid = players_order[0]
            emit("waitingForPlayers", {
                "message": "Waiting for one more person..."
            }, room=remaining_sid)

            return

def log_event(event_type, data=None):
    canvas_history.append((event_type, data or {}))

@socketio.on("startPath")
def handle_start_path(data):
    if request.sid == current_round["drawer"]:
        log_event("startPath", data)
        emit("startPath", data, broadcast=True, include_self=False)

@socketio.on("draw")
def handle_draw(data):
    if request.sid == current_round["drawer"]:
        log_event("draw", data)
        emit("draw", data, broadcast=True, include_self=False)

@socketio.on("dot")
def handle_dot(data):
    if request.sid == current_round["drawer"]:
        log_event("dot", data)
        emit("dot", data, broadcast=True, include_self=False)

@socketio.on("endPath")
def handle_end_path():
    if request.sid == current_round["drawer"]:
        emit("endPath", {}, broadcast=True, include_self=False)

@socketio.on("fill")
def handle_fill(data):
    if request.sid == current_round["drawer"]:
        log_event("fill", data)
        emit("fill", data, broadcast=True, include_self=False)

@socketio.on("undo")
def handle_undo():
    if request.sid != current_round["drawer"]:
        return

    # Helper to remove ONE complete operation
    def pop_one_action():
        if not canvas_history:
            return
        while canvas_history:
            event_type, _ = canvas_history.pop()
            if event_type in ("startPath", "dot", "fill"):
                break

    # Pop TWO full actions instead of one, temp fix undo bug?
    pop_one_action()
    pop_one_action()

    # Clear everyone’s canvas
    emit("clear", {}, broadcast=True)

    # Replay the remaining history
    for event_type, payload in canvas_history:
        emit(event_type, payload, broadcast=True)


@socketio.on("clear")
def handle_clear():
    if request.sid == current_round["drawer"]:
        canvas_history.clear()
        emit("clear", {}, broadcast=True, include_self=False)

@socketio.on("forceRoundEnd")
def handle_force_round_end():
    global current_drawer_index

    if request.sid != current_round["drawer"]:
        return
    
    if not current_round["active"]:
        return

    current_round["active"] = False
    current_drawer_index = (current_drawer_index + 1) % len(players_order)
    emit("chatMessage", {
        "type": "reveal",
        "word": current_round["prompt"],
        "sender_zone": 2
    }, broadcast=True)
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

            # Already guessed before? Ignore repeat guesses
            if sid not in current_round["correct_guessers"]:

                current_round["correct_guessers"].add(sid)

                ROUND_TIME = 20
                elapsed = time.time() - current_round["time_started"]
                remaining = max(0, ROUND_TIME - elapsed)
                percent_left = remaining / ROUND_TIME

                # Scoring rules
                if percent_left >= 0.80:
                    guesser_points = 3
                elif percent_left >= 0.40:
                    guesser_points = 2
                else:
                    guesser_points = 1

                players[sid]["score"] += guesser_points
                players[drawer_sid]["score"] += 1  # drawer always +1

                emit("chatMessage", {
                    "type": "correct",
                    "name": name,
                    "sender_zone": 2
                }, broadcast=True)

                emit("playerList", [
                    {
                        "name": p["name"],
                        "avatar": p["avatar"],
                        "score": p["score"]
                    }
                    for p in players.values()
                ], broadcast=True)

                # Check if all guessers finished
                guesser_count = len(players_order) - 1
                if len(current_round["correct_guessers"]) == guesser_count:
                    current_round["active"] = False
                    current_drawer_index = (current_drawer_index + 1) % len(players_order)
                    emit("chatMessage", {
                        "type": "reveal",
                        "word": current_round["prompt"],
                        "sender_zone": 2
                    }, broadcast=True)
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
