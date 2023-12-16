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

    def get_size(self) -> tuple[float, float]:
        widest_child = self.get_widest_child()
        min_width = widest_child.width() if widest_child else 100
        width = max(self.page.get_content_width() * 0.3, min_width)
        height = self.page.get_content_height()
        return width, height

    def show_add_player_ui(self):
        print("Add player UI")

    def update_children(self):
        current_game = self.game.current_game
        assert current_game
        self.clear_children()
        for player in current_game.players:
            self.add_children(PlayerListItem(self.game, player))

        self.add_children(
            Button(
                self.game,
                "+ Add player",
                self.show_add_player_ui,
                Container.AutoPlacement(),
            )
        )

    def __init__(self, game: Monopoly, page: TokenSelection):
        spawn_at = PointSpecifier(*page.get_content_start_point())
        self.page = page
        super().__init__(game, spawn_at, self.get_size, game.theme.BACKGROUND_ACCENT)
        self.tick_tasks.append(self.update_children)


class TokenSelection(Page):
    def __init__(self, game: Monopoly) -> None:
        super().__init__(game, "Select a token")
        self.page_header = Header(game)

        self.objects.extend([self.page_header, PlayerList(game, self)])
