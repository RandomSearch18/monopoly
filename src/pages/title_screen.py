from __future__ import annotations
from typing import TYPE_CHECKING
from components import Button, Header

from game_engine import (
    Page,
    PercentagePoint,
)

if TYPE_CHECKING:
    from main import Monopoly


class TitleScreen(Page):
    def __init__(self, game: Monopoly) -> None:
        super().__init__(game, "Title screen")
        self.page_header = Header(game, "Welcome to Monopoly")
        self.start_button = Button(
            game,
            "Start new game",
            game.start_new_game,
            PercentagePoint(0.5, 0.25),
        )

        self.objects.extend(
            [
                self.page_header,
                self.start_button,
            ]
        )
