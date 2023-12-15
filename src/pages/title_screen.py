from __future__ import annotations
from typing import TYPE_CHECKING
from components import Button, Header, Text

from game_engine import (
    CENTER,
    START,
    Game,
    Page,
    Percent,
    PercentagePoint,
    Pixels,
    PointSpecifier,
    PointSpecifier,
)

if TYPE_CHECKING:
    from main import Monopoly


class TitleScreen(Page):
    def __init__(self, game: Monopoly) -> None:
        super().__init__(game, "Title screen")
        self.page_header = Header(game, "Welcome to Monopoly")
        self.start_button = Button(
            game,
            "Start",
            lambda: game.token_selection.activate(),
            PercentagePoint(0.5, 0.25),
        )

        self.objects.extend(
            [
                self.page_header,
                self.start_button,
            ]
        )
