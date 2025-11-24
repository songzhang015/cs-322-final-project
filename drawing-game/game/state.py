# state.py
from services.PackService import pack_service

class GameState:
    def __init__(self):
        self.CURRENT_PACK = "standard-pack"
        self.words = pack_service.get_pack(self.CURRENT_PACK)["words"]

        self.players = {}
        self.players_order = []
        self.current_drawer_index = 0
        self.ROUND_TOTAL_SECONDS = 100

        self.canvas_history = []

        self.current_round = {
            "drawer": None,
            "prompt": None,
            "active": False,
            "correct_guessers": set(),
            "time_started": None,
            "revealed_indices": set(),
            "max_reveals": 0,
            "guess_reveals_done": 0,
        }

# SINGLE SHARED INSTANCE IMPORTED EVERYWHERE
game_state = GameState()
