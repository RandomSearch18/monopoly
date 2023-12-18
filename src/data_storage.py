from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict


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

    def __str__(self) -> str:
        return self.nickname


class SavedGame(BaseModel):
    started_at: datetime
    is_saved_to_disk: bool
    players: list[Player]

    def get_unused_tokens(self) -> list[Token]:
        return [
            token
            for token in Token
            if token not in [player.token for player in self.players]
        ]

    def get_next_unused_token(self) -> Token:
        unused_tokens = self.get_unused_tokens()
        if not unused_tokens:
            raise RuntimeError("No more tokens available")
        return unused_tokens[0]

    def get_next_default_player_name(self) -> str:
        return f"Player {len(self.players) + 1}"

    def __str__(self):
        return self.started_at.strftime("Game<%Y-%m-%d %H:%M:%S>")
