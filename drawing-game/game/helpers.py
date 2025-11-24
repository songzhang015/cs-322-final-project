#  Helper functions
from game.state import game_state

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
    Returns something like: A _ _ L E  for 'APPLE'.
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

def log_event(event_type, data=None):
    game_state.canvas_history.append((event_type, data or {}))