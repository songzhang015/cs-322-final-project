import time
import random
from flask_socketio import emit
from extensions.socketio import socketio
from game.state import game_state
from game.helpers import compute_max_reveals
from game.reveal import manage_time_reveals

def reset_lobby():
    game_state.current_round["drawer"] = None
    game_state.current_round["prompt"] = None
    game_state.current_round["active"] = False
    game_state.current_round["correct_guessers"] = set()
    game_state.current_round["time_started"] = None
    game_state.current_round["revealed_indices"] = set()
    game_state.current_round["max_reveals"] = 0
    game_state.current_round["guess_reveals_done"] = 0

    game_state.current_drawer_index = 0

    # Clear canvas for all players
    emit("clear", {}, broadcast=True)

    # Tell clients to stop timer & reset header
    emit("lobbyReset", {}, broadcast=True)


def start_new_round():
    if not game_state.players_order:
        print("No players available to start round.")
        return

    # Safety wrap
    if game_state.current_drawer_index >= len(game_state.players_order):
        game_state.current_drawer_index = 0

    drawer_sid = game_state.players_order[game_state.current_drawer_index]
    prompt = random.choice(game_state.words)

    game_state.current_round["drawer"] = drawer_sid
    game_state.current_round["prompt"] = prompt
    game_state.current_round["active"] = True
    game_state.current_round["correct_guessers"] = set()

    # Reveal state for this word
    word_len = len(prompt)
    game_state.current_round["revealed_indices"] = set()
    game_state.current_round["max_reveals"] = compute_max_reveals(word_len)
    game_state.current_round["guess_reveals_done"] = 0

    print("Round initializing...")
    print(f"Drawer: {game_state.players[drawer_sid]['name']}  Prompt: {prompt}")

    game_state.canvas_history.clear()
    # Immediate UI clear
    emit("clear", {}, broadcast=True)

    emit("roundStarting", {}, broadcast=True)

    socketio.sleep(3)

    game_state.current_round["time_started"] = time.time()

    for sid in game_state.players:
        emit("roundStarted", {
            "role": "drawer" if sid == drawer_sid else "guesser",
            "startTime": game_state.current_round["time_started"]
        }, room=sid)

    # Drawer prompt
    emit("roundPrompt", {
        "role": "drawer",
        "prompt": prompt
    }, room=drawer_sid)

    # Guessers get length
    for sid in game_state.players:
        if sid != drawer_sid:
            emit("roundPrompt", {
                "role": "guesser",
                "length": len(prompt)
            }, room=sid)

    # Start background task for time-based reveals
    socketio.start_background_task(
        manage_time_reveals,
        game_state.current_round["time_started"],
        word_len
    )