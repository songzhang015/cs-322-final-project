from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from pymongo import MongoClient
import random
import time
from blueprints.packs.Routes import packs_bp
from services.PackService import pack_service

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app, cors_allowed_origins="*")

ROUND_TOTAL_SECONDS = 100
CURRENT_PACK = "standard-pack"
words = pack_service.get_pack(CURRENT_PACK)["words"]

@app.route("/")
def index():
    return render_template("index.html"), 200

app.register_blueprint(packs_bp, url_prefix="/api")

players = {}
players_order = []
current_drawer_index = 0

canvas_history = []

current_round = {
    "drawer": None,
    "prompt": None,
    "active": False,
    "correct_guessers": set(),
    "time_started": None,
    "revealed_indices": set(),
    "max_reveals": 0,
    "guess_reveals_done": 0,
}

# =========================
#  LETTER REVEAL HELPERS
# =========================

def compute_max_reveals(word_len: int) -> int:
    if word_len <= 4:
        return 2
    if word_len == 5:
        return 3
    if word_len == 6:
        return 4
    if word_len == 7:
        return 4
    if word_len == 8:
        return 5
    if word_len == 9:
        return 6
    if word_len == 10:
        return 6
    return 7


def build_masked_word(prompt: str, revealed_indices: set) -> str:
    """
    Returns something like: A _ _ L E  for 'APPLE' with indices {0, 3}.
    Non-alpha characters (if you add any later) will always show.
    """
    chars = []
    for i, ch in enumerate(prompt):
        if not ch.isalpha():
            chars.append(ch)
        elif i in revealed_indices:
            chars.append(ch)
        else:
            chars.append("_")
    return " ".join(chars)


def reveal_random_letters(num_letters: int):
    """
    Core reveal function.
    - Respects max_reveals cap.
    - Does not re-reveal already revealed letters.
    - Broadcasts 'letterReveal' to guessers with the updated mask.
    """
    if not current_round["active"] or not current_round["prompt"]:
        return

    word = current_round["prompt"]
    word_len = len(word)

    # Consider only alphabetic positions as revealable letters
    all_positions = [i for i, ch in enumerate(word) if ch.isalpha()]
    unrevealed = [i for i in all_positions if i not in current_round["revealed_indices"]]

    if not unrevealed:
        return

    already_revealed_count = len(current_round["revealed_indices"])
    remaining_capacity = current_round["max_reveals"] - already_revealed_count
    if remaining_capacity <= 0:
        return

    to_reveal = min(num_letters, remaining_capacity, len(unrevealed))
    if to_reveal <= 0:
        return

    chosen = random.sample(unrevealed, to_reveal)
    current_round["revealed_indices"].update(chosen)

    masked = build_masked_word(word, current_round["revealed_indices"])

    drawer_sid = current_round["drawer"]

    # Send masked word to all guessers
    for sid in players:
        if sid != drawer_sid:
            socketio.emit("letterReveal", {
                "mask": masked
            }, room=sid)


def manage_time_reveals(start_time_snapshot: float, word_len: int):
    """
    Time-based reveals at remaining 75s, 50s, 25s (assuming 100s total).
    That corresponds to elapsed times of 25s, 50s, 75s.
    """

    # (elapsed_target, label)
    thresholds = [
        (ROUND_TOTAL_SECONDS - 75, "75"),  # 25s elapsed, 75s remaining
        (ROUND_TOTAL_SECONDS - 50, "50"),  # 50s elapsed, 50s remaining
        (ROUND_TOTAL_SECONDS - 25, "25"),  # 75s elapsed, 25s remaining
    ]

    last_elapsed = 0
    for elapsed_target, label in thresholds:
        sleep_for = elapsed_target - last_elapsed
        if sleep_for > 0:
            socketio.sleep(sleep_for)
        last_elapsed = elapsed_target

        # If round ended or a new round started, stop this task
        if (not current_round["active"] or
                current_round["time_started"] != start_time_snapshot):
            return

        # Decide how many letters to reveal per timing rule
        if label == "75":
            # Reveal at 75 seconds remaining → 1 letter
            reveal_random_letters(1)

        elif label == "50":
            # Reveal at 50 seconds remaining:
            # Base 1; if length 9+ AND no one has guessed yet → up to 2 letters
            base = 1
            extra = 1 if (word_len >= 9 and not current_round["correct_guessers"]) else 0
            reveal_random_letters(base + extra)

        elif label == "25":
            # Reveal at 25 seconds remaining:
            # Base 1; if length 9+ → up to 2 letters
            base = 1
            extra = 1 if word_len >= 9 else 0
            reveal_random_letters(base + extra)


def reset_lobby():
    global current_drawer_index

    current_round["drawer"] = None
    current_round["prompt"] = None
    current_round["active"] = False
    current_round["correct_guessers"] = set()
    current_round["time_started"] = None

    # NEW: reset reveal state
    current_round["revealed_indices"] = set()
    current_round["max_reveals"] = 0
    current_round["guess_reveals_done"] = 0

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

    # NEW: init reveal state for this word
    word_len = len(prompt)
    current_round["revealed_indices"] = set()
    current_round["max_reveals"] = compute_max_reveals(word_len)
    current_round["guess_reveals_done"] = 0

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

    # NEW: start background task for time-based reveals
    socketio.start_background_task(
        manage_time_reveals,
        current_round["time_started"],
        word_len
    )





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
        ROUND_TIME = 100

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

            # NEW: if some letters are already revealed, send current mask to late-joining guesser
            if current_round["revealed_indices"]:
                masked = build_masked_word(prompt, current_round["revealed_indices"])
                emit("letterReveal", {
                    "mask": masked
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

        # >>> NEW: If the drawer left mid-round, auto-advance <<<
        if current_round["active"] and sid == current_round["drawer"]:
            print("Drawer left mid-round. Advancing to next player.")

            # Reveal the word
            emit("chatMessage", {
                "type": "reveal",
                "word": current_round["prompt"],
                "sender_zone": 2
            }, broadcast=True)

            # Fix drawer index if needed
            if players_order:
                current_drawer_index = current_drawer_index % len(players_order)
            else:
                current_drawer_index = 0

            current_round["active"] = False

            # Start next round
            start_new_round()
            return

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
    prompt = current_round["prompt"].lower() if current_round["prompt"] else ""

    # ------------------------------------------
    # STEP 1 — HANDLE CORRECT GUESS FIRST
    # ------------------------------------------
    if current_round["active"] and current_round["prompt"]:
        if sid != drawer_sid and message.lower() == prompt:

            # Already guessed before? Ignore repeat guesses
            if sid not in current_round["correct_guessers"]:

                current_round["correct_guessers"].add(sid)

                ROUND_TIME = 100
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

                # --- NEW: guess-percentage-based reveals ---
                guesser_count = len(players_order) - 1
                if guesser_count > 0:
                    ratio = len(current_round["correct_guessers"]) / guesser_count

                    # 70% threshold → 2nd reveal (if not already done)
                    if ratio >= 0.7 and current_round["guess_reveals_done"] < 2:
                        reveal_random_letters(1)
                        current_round["guess_reveals_done"] = 2

                    # 40% threshold → 1st reveal (if not already done)
                    elif ratio >= 0.4 and current_round["guess_reveals_done"] < 1:
                        reveal_random_letters(1)
                        current_round["guess_reveals_done"] = 1

                # Check if all guessers finished
                if guesser_count > 0 and len(current_round["correct_guessers"]) == guesser_count:
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
