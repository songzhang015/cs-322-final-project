from flask import request
from flask_socketio import emit
from extensions.socketio import socketio
import time

from game.state import game_state

from game.helpers import (
    build_masked_word,
    log_event
)

from game.manager import (
    start_new_round,
    reset_lobby
)

from game.reveal import (
    reveal_random_letters
)


@socketio.on("join")
def handle_join(data):
    sid = request.sid
    name = data.get("name")
    avatar = data.get("avatar")
    client_id = data.get("id")

    if not name or not avatar:
        return

    game_state.players[sid] = {
        "client_id": client_id,
        "name": name,
        "avatar": avatar,
        "score": 0
    }

    game_state.players_order.append(sid)

    print(f"{name} joined with SID {sid}")
    print("Current players order:", game_state.players_order)

    # Sync late joiners
    if game_state.current_round["active"]:
        ROUND_TIME = 100

        elapsed = int(time.time() - game_state.current_round["time_started"])
        remaining = max(0, ROUND_TIME - elapsed)

        drawer_sid = game_state.current_round["drawer"]
        prompt = game_state.current_round["prompt"]

        emit("roundStarted", {
            "role": "drawer" if sid == drawer_sid else "guesser",
            "startTime": game_state.current_round["time_started"]
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

            # If some letters are already revealed, send current mask to late-joining guesser
            if game_state.current_round["revealed_indices"]:
                masked = build_masked_word(prompt, game_state.current_round["revealed_indices"])
                emit("letterReveal", {
                    "mask": masked
                }, room=sid)

        for event_type, payload in game_state.canvas_history:
            emit(event_type, payload, room=sid)

        emit("playerList", [
            {
                "name": p["name"],
                "avatar": p["avatar"],
                "score": p["score"]
            }
            for p in game_state.players.values()
        ], broadcast=True)

        return

    # First player
    if len(game_state.players_order) == 1:
        emit("waitingForPlayers", {
            "message": "Waiting for one more person..."
        }, room=sid)
        return

    # Second player -> start the first round
    if len(game_state.players_order) == 2:
        game_state.current_drawer_index = 0
        start_new_round()

    emit("playerList", [
        {
            "name": p["name"],
            "avatar": p["avatar"],
            "score": p["score"]
        }
        for p in game_state.players.values()
    ], broadcast=True)


@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid

    if sid in game_state.players:
        name = game_state.players[sid]["name"]

        # Remove from players & ordering
        if sid in game_state.players_order:
            idx = game_state.players_order.index(sid)
            game_state.players_order.remove(sid)

            # Adjust drawer index if necessary
            if idx < game_state.current_drawer_index:
                game_state.current_drawer_index -= 1
            if game_state.current_drawer_index >= len(game_state.players_order) and game_state.players_order:
                game_state.current_drawer_index = 0

        del game_state.players[sid]

        print(f"{name} left. Remaining players: {len(game_state.players)}")

        # Left game
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
            for p in game_state.players.values()
        ], broadcast=True)

        # If the drawer left mid-round, auto-advance
        if game_state.current_round["active"] and sid == game_state.current_round["drawer"]:
            print("Drawer left mid-round. Advancing to next player.")

            # Reveal the word
            emit("chatMessage", {
                "type": "reveal",
                "word": game_state.current_round["prompt"],
                "sender_zone": 2
            }, broadcast=True)

            # Fix drawer index if needed
            if game_state.players_order:
                game_state.current_drawer_index = game_state.current_drawer_index % len(game_state.players_order)
            else:
                game_state.current_drawer_index = 0

            game_state.current_round["active"] = False

            # Start next round
            start_new_round()
            return

        # Lobby reset logic
        if len(game_state.players_order) == 1:
            if game_state.current_round["active"] and game_state.current_round["prompt"]:
                emit("chatMessage", {
                    "type": "reveal",
                    "word": game_state.current_round["prompt"],
                    "sender_zone": 2
                }, broadcast=True)
            reset_lobby()

            remaining_sid = game_state.players_order[0]
            emit("waitingForPlayers", {
                "message": "Waiting for one more person..."
            }, room=remaining_sid)

            return


@socketio.on("startPath")
def handle_start_path(data):
    if request.sid == game_state.current_round["drawer"]:
        log_event("startPath", data)
        emit("startPath", data, broadcast=True, include_self=False)


@socketio.on("draw")
def handle_draw(data):
    if request.sid == game_state.current_round["drawer"]:
        log_event("draw", data)
        emit("draw", data, broadcast=True, include_self=False)


@socketio.on("dot")
def handle_dot(data):
    if request.sid == game_state.current_round["drawer"]:
        log_event("dot", data)
        emit("dot", data, broadcast=True, include_self=False)


@socketio.on("endPath")
def handle_end_path():
    if request.sid == game_state.current_round["drawer"]:
        emit("endPath", {}, broadcast=True, include_self=False)


@socketio.on("fill")
def handle_fill(data):
    if request.sid == game_state.current_round["drawer"]:
        log_event("fill", data)
        emit("fill", data, broadcast=True, include_self=False)


@socketio.on("undo")
def handle_undo():
    if request.sid != game_state.current_round["drawer"]:
        return

    # Helper to remove ONE complete operation
    def pop_one_action():
        if not game_state.canvas_history:
            return
        while game_state.canvas_history:
            event_type, _ = game_state.canvas_history.pop()
            if event_type in ("startPath", "dot", "fill"):
                break

    # Pop TWO full actions instead of one, temp fix undo bug?
    pop_one_action()
    pop_one_action()

    # Clear everyone’s canvas
    emit("clear", {}, broadcast=True)

    # Replay the remaining history
    for event_type, payload in game_state.canvas_history:
        emit(event_type, payload, broadcast=True)


@socketio.on("clear")
def handle_clear():
    if request.sid == game_state.current_round["drawer"]:
        game_state.canvas_history.clear()
        emit("clear", {}, broadcast=True, include_self=False)


@socketio.on("forceRoundEnd")
def handle_force_round_end():
    if request.sid != game_state.current_round["drawer"]:
        return
    
    if not game_state.current_round["active"]:
        return

    game_state.current_round["active"] = False
    game_state.current_drawer_index = (game_state.current_drawer_index + 1) % len(game_state.players_order)
    emit("chatMessage", {
        "type": "reveal",
        "word": game_state.current_round["prompt"],
        "sender_zone": 2
    }, broadcast=True)
    start_new_round()


@socketio.on("chatMessage")
def handle_chat_message(data):
    sid = request.sid
    if sid not in game_state.players:
        return

    message = data.get("message", "").strip()
    name = game_state.players[sid]["name"]

    drawer_sid = game_state.current_round["drawer"]
    prompt = game_state.current_round["prompt"].lower() if game_state.current_round["prompt"] else ""

    # STEP 1 — HANDLE CORRECT GUESS FIRST
    if game_state.current_round["active"] and game_state.current_round["prompt"]:
        if sid != drawer_sid and message.lower() == prompt:

            # Already guessed before? Ignore repeat guesses
            if sid not in game_state.current_round["correct_guessers"]:

                game_state.current_round["correct_guessers"].add(sid)

                ROUND_TIME = 100
                elapsed = time.time() - game_state.current_round["time_started"]
                remaining = max(0, ROUND_TIME - elapsed)
                percent_left = remaining / ROUND_TIME

                # Scoring rules
                if percent_left >= 0.80:
                    guesser_points = 3
                elif percent_left >= 0.40:
                    guesser_points = 2
                else:
                    guesser_points = 1

                game_state.players[sid]["score"] += guesser_points
                game_state.players[drawer_sid]["score"] += 1  # drawer always +1

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
                    for p in game_state.players.values()
                ], broadcast=True)

                # guess-percentage-based reveals
                guesser_count = len(game_state.players_order) - 1
                if guesser_count > 0:
                    ratio = len(game_state.current_round["correct_guessers"]) / guesser_count

                    # 70% threshold → 2nd reveal (if not already done)
                    if ratio >= 0.7 and game_state.current_round["guess_reveals_done"] < 2:
                        reveal_random_letters(1)
                        game_state.current_round["guess_reveals_done"] = 2

                    # 40% threshold → 1st reveal (if not already done)
                    elif ratio >= 0.4 and game_state.current_round["guess_reveals_done"] < 1:
                        reveal_random_letters(1)
                        game_state.current_round["guess_reveals_done"] = 1

                # Check if all guessers finished
                if guesser_count > 0 and len(game_state.current_round["correct_guessers"]) == guesser_count:
                    game_state.current_round["active"] = False
                    game_state.current_drawer_index = (game_state.current_drawer_index + 1) % len(game_state.players_order)
                    emit("chatMessage", {
                        "type": "reveal",
                        "word": game_state.current_round["prompt"],
                        "sender_zone": 2
                    }, broadcast=True)
                    start_new_round()

                return

    # STEP 2 — ROUTE MESSAGE BASED ON UPDATED ZONES
    # Determine sender zone
    sender_is_drawer = (sid == drawer_sid)
    sender_has_guessed = (sid in game_state.current_round["correct_guessers"])

    sender_zone = 2 if (sender_is_drawer or sender_has_guessed) else 1

    # ZONE 1: only unguessed guessers receive zone1 messages
    if sender_zone == 1:
        for sid2 in game_state.players:
            if sid2 != drawer_sid and sid2 not in game_state.current_round["correct_guessers"]:
                emit("chatMessage", {
                    "name": name,
                    "message": message,
                    "sender_zone": 1
                }, room=sid2)

    # ZONE 2: drawer + guessed guessers receive ALL messages
    for sid2 in game_state.players:
        if sid2 == drawer_sid or sid2 in game_state.current_round["correct_guessers"]:
            emit("chatMessage", {
                "name": name,
                "message": message,
                "sender_zone": sender_zone
            }, room=sid2)