from __future__ import annotations
from typing import TYPE_CHECKING

from components import Button, Container, Header
from data_storage import Player
from game_engine import START, GameObject, Page, Pixels, PointSpecifier

if TYPE_CHECKING:
    from main import Monopoly


class PlayerListItem(Button):
    """A clickable entry in the player list"""

    def __init__(self, game: Monopoly, player: Player):
        super().__init__(
            game, player.nickname, self.on_click, Container.AutoPlacement()
        )
        self.player = player

    def on_click(self):
        print(f"Clicked on {self.player}")


class PlayerList(Container):
    """A sidebar showing any players that have been added to the game"""


class TokenSelection(Page):
    def __init__(self, game: Monopoly) -> None:
        super().__init__(game, "Select a token")
        title_position = PointSpecifier(
            Pixels(5, position=START), Pixels(5, position=START)
        )
        # self.page_title = Text(game, lambda: "Select a token", title_position)
        self.page_header = Header(game)

        self.objects.extend([self.page_header])
