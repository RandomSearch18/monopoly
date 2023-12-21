from __future__ import annotations
from typing import TYPE_CHECKING

from pygame import Color

from components import Button, Container, Header, TextObject
from data_storage import Player
from game_engine import (
    START,
    BelowObject,
    BelowPoint,
    Game,
    GameObject,
    Page,
    Percent,
    Pixels,
    PointSpecifier,
    RightOfObject,
)

if TYPE_CHECKING:
    from main import Monopoly


class PlayerListItem(Button):
    """A clickable entry in the player list"""

    def __init__(self, game: Monopoly, player: Player):
        super().__init__(
            game, player.nickname, self.on_click, Container.AutoPlacement(5)
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
        initial_name = current_game.data.get_next_default_player_name()
        initial_token = current_game.data.get_unused_token()
        current_game.add_player(Player(nickname=initial_name, token=initial_token))

    def update_children(self):
        current_game = self.game.current_game
        assert current_game
        existing_player_items = [
            child for child in self.list_children() if isinstance(child, PlayerListItem)
        ]
        for player in current_game.data.players:
            if player not in [child.player for child in existing_player_items]:
                # Add a child for this player, as it aren't in the UI yet
                print(f"PlayerList: Adding list item for {player}")
                self.add_children(PlayerListItem(self.game, player))
        for child in existing_player_items:
            if child.player not in current_game.data.players:
                # Remove this child from the UI, as the corrresponding player doesn't exist anymore
                print(
                    f"PlayerList: Removing list item for {child.player} (hint: this shouldn't happen yet)"
                )
                self.remove_child(child)

        should_show_add_player_button = current_game.data.get_free_player_slots() > 0
        # Add the "Add player" button if it doesn't exist yet (and there are free slots)
        if not self.add_player_button and should_show_add_player_button:
            print(f'PlayerList: Adding "+ Player" button')
            self.add_player_button = Button(
                self.game,
                "+ Add player",
                self.add_new_player,
                Container.AutoPlacement(),
            )
            self.add_children(self.add_player_button)

        # Remove the "Add player" button if we're now at max capacity
        if self.add_player_button and not should_show_add_player_button:
            print(f'PlayerList: Removing "+ Player" button')
            self.remove_child(self.add_player_button)
            self.add_player_button = None

    def __init__(self, game: Monopoly, page: TokenSelection):
        spawn_at = page.get_content_start_point()
        self.page = page
        super().__init__(
            game, spawn_at, self.get_size, game.theme.BACKGROUND_ACCENT, padding_top=10
        )
        self.add_player_button: Button | None = None
        self.tick_tasks.append(self.update_children)


class HintText(TextObject):
    """Displays a hint to the right of the sidebar prompting the user to select a player"""

    def get_spawn_point(self, game: Game, page: TokenSelection) -> PointSpecifier:
        x = RightOfObject(page.player_list, 10)
        assert page.page_header
        y = BelowObject(page.page_header, 10)

        return PointSpecifier(x, y)

    def __init__(self, game: Monopoly, page: TokenSelection):
        super().__init__(
            game,
            self.get_content,
            self.get_spawn_point(game, page),
            break_line_at=Percent(1.0),
        )

    def get_content(self) -> str:
        current_game = self.game.current_game
        if not current_game:
            return "Load a saved game or start a new one first!"  # This should never end up being shown in-game
        if not current_game.data.players:
            return "Get the game started by adding players with the button on the left."
        if not current_game.data.any_players_have_chosen_tokens():
            return "Click on a player in the sidebar to customise their token."
        # This should never get shown either:
        return "Start the game once everyone's ready!"


class TokenSelection(Page):
    def __init__(self, game: Monopoly) -> None:
        super().__init__(game, "Choose tokens")
        self.page_header = Header(game)
        self.player_list = PlayerList(game, self)
        self.hint_text = HintText(game, self)
        self.objects.extend([self.page_header, self.player_list, self.hint_text])
