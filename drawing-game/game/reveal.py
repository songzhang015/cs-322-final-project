import random
from extensions.socketio import socketio
from game.state import game_state
from game.helpers import build_masked_word

def reveal_random_letters(num_letters: int):
    """
    Core reveal function.
    - Respects max_reveals cap.
    - Does not re-reveal already revealed letters.
    """
    if not game_state.current_round["active"] or not game_state.current_round["prompt"]:
        return

    word = game_state.current_round["prompt"]

    # Consider only alphabetic positions as revealable letters
    all_positions = [i for i, ch in enumerate(word) if ch.isalpha()]
    unrevealed = [i for i in all_positions if i not in game_state.current_round["revealed_indices"]]

    if not unrevealed:
        return

    already_revealed_count = len(game_state.current_round["revealed_indices"])
    remaining_capacity = game_state.current_round["max_reveals"] - already_revealed_count
    if remaining_capacity <= 0:
        return

    to_reveal = min(num_letters, remaining_capacity, len(unrevealed))
    if to_reveal <= 0:
        return

    chosen = random.sample(unrevealed, to_reveal)
    game_state.current_round["revealed_indices"].update(chosen)

    masked = build_masked_word(word, game_state.current_round["revealed_indices"])

    drawer_sid = game_state.current_round["drawer"]

    # Send masked word to all guessers
    for sid in game_state.players:
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
        (game_state.ROUND_TOTAL_SECONDS - 75, "75"),  # 25s elapsed, 75s remaining
        (game_state.ROUND_TOTAL_SECONDS - 50, "50"),  # 50s elapsed, 50s remaining
        (game_state.ROUND_TOTAL_SECONDS - 25, "25"),  # 75s elapsed, 25s remaining
    ]

    last_elapsed = 0
    for elapsed_target, label in thresholds:
        sleep_for = elapsed_target - last_elapsed
        if sleep_for > 0:
            socketio.sleep(sleep_for)
        last_elapsed = elapsed_target

        # If round ended or a new round started, stop this task
        if (not game_state.current_round["active"] or
                game_state.current_round["time_started"] != start_time_snapshot):
            return

        # Decide how many letters to reveal per timing rule
        if label == "75":
            # Reveal at 75 seconds remaining → 1 letter
            reveal_random_letters(1)

        elif label == "50":
            # Reveal at 50 seconds remaining:
            # Base 1; if length 9+ AND no one has guessed yet → up to 2 letters
            base = 1
            extra = 1 if (word_len >= 9 and not game_state.current_round["correct_guessers"]) else 0
            reveal_random_letters(base + extra)

        elif label == "25":
            # Reveal at 25 seconds remaining:
            # Base 1; if length 9+ → up to 2 letters
            base = 1
            extra = 1 if word_len >= 9 else 0
            reveal_random_letters(base + extra)
