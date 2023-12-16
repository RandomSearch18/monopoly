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

    def add_new_player(self):
        print("New player button clicked")
        current_game = self.game.current_game
        assert current_game
        initial_token = current_game.get_next_unused_token()
        current_game.players.append(Player(nickname="New player", token=initial_token))

    def update_children(self):
        current_game = self.game.current_game
        assert current_game
        existing_player_items = [
            child for child in self.list_children() if isinstance(child, PlayerListItem)
        ]
        for player in current_game.players:
            if player not in [child.player for child in existing_player_items]:
                # Add a child for this player, as it aren't in the UI yet
                self.add_children(PlayerListItem(self.game, player))
        for child in existing_player_items:
            if child.player not in current_game.players:
                # Remove this child from the UI, as the corrresponding player doesn't exist anymore
                self.remove_child(child)

        if not self.list_children():
            self.add_children(
                Button(
                    self.game,
                    "+ Add player",
                    self.add_new_player,
                    Container.AutoPlacement(),
                )
            )
        # print(self.list_children())

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
