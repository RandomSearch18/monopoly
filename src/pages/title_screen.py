from __future__ import annotations
from typing import TYPE_CHECKING
from components import Button, Text

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
        title_position = PointSpecifier(
            Percent(0.50, position=CENTER), Pixels(5, position=START)
        )
        self.title_text = Text(game, lambda: self.game.title, title_position)
        self.start_button = Button(
            game,
            "Start",
            lambda: game.token_selection.activate(),
            PercentagePoint(0.5, 0.25),
        )

        self.objects.extend(
            [
                self.title_text,
                self.start_button,
            ]
        )
