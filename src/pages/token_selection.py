from __future__ import annotations
from typing import TYPE_CHECKING

from pygame import Color

from components import Button, Container, Header
from data_storage import Player
from game_engine import START, BelowObject, GameObject, Page, Pixels, PointSpecifier

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
    """A sidebar showing a list of any players that have been added to the game"""

    def __init__(self, game: Monopoly, page: TokenSelection):
        spawn_at = PointSpecifier(*page.get_content_start_point())
        super().__init__(
            game,
            spawn_at,
            (page.get_content_width() * 0.25, page.get_content_height()),
            Color("grey"),
        )


class TokenSelection(Page):
    def __init__(self, game: Monopoly) -> None:
        super().__init__(game, "Select a token")
        self.page_header = Header(game)

        self.objects.extend([self.page_header, PlayerList(game, self)])
