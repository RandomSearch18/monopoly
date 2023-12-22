from datetime import datetime
from enum import Enum
import random
from pydantic import BaseModel


class Token(Enum):
    """A Monopoly token, i.e. a small model that represents each player"""

    BATTLESHIP = "battleship"
    THIMBLE = "thimble"
    WHEELBARROW = "wheelbarrow"
    CAT = "cat"
    DOG = "dog"
    RACE_CAR = "race car"
    TOP_HAT = "top hat"


class Player(BaseModel):
    nickname: str
    token: Token
    has_manually_selected_token: bool = False

    def set_token(self, token: Token):
        self.token = token
        self.has_manually_selected_token = True

    def get_nickname(self) -> str:
        return self.nickname

    def __str__(self) -> str:
        return self.get_nickname()


class SavedGameData(BaseModel):
    started_at: datetime
    is_saved_to_disk: bool
    players: list[Player]
    max_player_count: int = 6
    min_player_count: int = 2

    def get_unused_tokens(self) -> list[Token]:
        return [
            token
            for token in Token
            if token not in [player.token for player in self.players]
        ]

    def get_unused_token(self) -> Token:
        """Returns a random token that isn't already assigned to a player"""
        unused_tokens = self.get_unused_tokens()
        if not unused_tokens:
            raise RuntimeError("No more tokens available")
        return random.choice(unused_tokens)

    def get_next_default_player_name(self) -> str:
        return f"Player {len(self.players) + 1}"

    def get_max_players(self) -> int:
        available_tokens_count = len(Token)
        return min(available_tokens_count, self.max_player_count)

    def get_min_players(self) -> int:
        return self.min_player_count

    def get_free_player_slots(self) -> int:
        return self.get_max_players() - len(self.players)

    def any_players_have_chosen_tokens(self) -> bool:
        return any(player.has_manually_selected_token for player in self.players)

    def ready_to_start(self) -> bool:
        player_count = len(self.players)
        return self.get_min_players() <= player_count <= self.get_max_players()

    def __str__(self):
        return self.started_at.strftime("Game<%Y-%m-%d %H:%M:%S>")
