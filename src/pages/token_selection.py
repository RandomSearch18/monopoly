from __future__ import annotations
from copy import copy
from typing import TYPE_CHECKING, Callable

from components import Button, Container, Header, TextObject
from data_storage import Player, Token
from events import GameEvent
from game_engine import (
    END,
    BelowObject,
    CenterAlignedToObject,
    Corner,
    Page,
    Percent,
    Pixels,
    PointSpecifier,
    RightOfObject,
)

if TYPE_CHECKING:
    from main import Monopoly, SavedGameManager


class PlayerListItem(Button):
    """A clickable entry in the player list"""

    def __init__(self, game: Monopoly, page: TokenSelection, player: Player):
        super().__init__(
            game, player.nickname, self.on_click, Container.AutoPlacement(5)
        )
        self.page = page
        self.player = player

    def on_click(self):
        self.page.show_token_selection_pane(self.player)


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
        current_game.add_player(Player(nickname=initial_name))

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
                self.add_children(PlayerListItem(self.game, self.page, player))
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

        if current_game.data.ready_to_start() and not self.start_game_button:
            print(f"PlayerList: Adding start-game button")
            self.start_game_button = Button(
                self.game,
                "Start game",
                print,
                PointSpecifier(
                    CenterAlignedToObject(self, self.width),
                    Pixels(10, outer_edge=END, position=END),
                ),
            )
            self.add_children(self.start_game_button)

        if self.start_game_button and not current_game.data.ready_to_start():
            print(f"PlayerList: Removing start-game button")
            self.remove_child(self.start_game_button)
            self.start_game_button = None

    def __init__(self, game: Monopoly, page: TokenSelection):
        spawn_at = page.get_content_start_point()
        self.page = page
        super().__init__(
            game, spawn_at, self.get_size, game.theme.BACKGROUND_ACCENT, padding_top=10
        )
        self.add_player_button: Button | None = None
        self.start_game_button: Button | None = None
        self.tick_tasks.append(self.update_children)


class TokenSelectionButton(Button):
    def __init__(
        self,
        current_game: SavedGameManager,
        token_selection_pane: TokenSelectionPane,
        token: Token,
    ):
        super().__init__(
            token_selection_pane.game,
            token.value.capitalize(),
            self.on_selection,
            Container.AutoPlacement(5),
            is_disabled=self.is_disabled,
        )
        self.current_game = current_game
        self.token_selection_pane = token_selection_pane
        self.token = copy(token)

    def is_disabled(self):
        return self.token in [player.token for player in self.current_game.data.players]

    def on_selection(self):
        print(f"Emitting selected {self.token}")
        self.token_selection_pane.events.emit(GameEvent.TOKEN_SELECTED, self.token)


class TokenSelectionButtons(Container):
    def get_size(self) -> tuple[float, float]:
        total_height = sum(child.height() for child in self.list_children())
        widest_child = self.get_widest_child()
        total_width = widest_child.width() if widest_child else 0
        return total_width, total_height

    def __init__(
        self,
        game: Monopoly,
        page: TokenSelection,
        parent_pane: TokenSelectionPane,
        spawn_at: PointSpecifier,
        on_token_selection: Callable[[Token], None],
    ):
        self.page = page
        self.parent_pane = parent_pane
        super().__init__(game, spawn_at, self.get_size)
        self.on_token_selection = on_token_selection
        self.events.on(GameEvent.BEFORE_SPAWN, self.on_spawn)

    def on_spawn(self):
        current_game = self.game.current_game
        assert current_game
        token_buttons = [
            TokenSelectionButton(current_game, self.parent_pane, token)
            for token in Token
        ]
        self.add_children(*token_buttons)


class TokenSelectionPane(Container):
    def get_size(self) -> tuple[float, float]:
        total_height = sum(child.height() for child in self.list_children())
        widest_child = self.get_widest_child()
        total_width = widest_child.width() if widest_child else 0
        return total_width, total_height

    def on_token_selection(self, token: Token):
        print(f"TokenSelectionPane: {self.player} selected {token}")
        assert self.game.current_game
        self.game.current_game.set_player_token(self.player, token)

    def __init__(self, game: Monopoly, page: TokenSelection, player: Player):
        self.player = player
        print(player)
        self.page = page
        super().__init__(game, page.get_main_pane_start_point(), self.get_size)

        self.heading = TextObject(
            self.game,
            self.player.get_nickname,
            Container.AutoPlacement(),
            break_line_at=Percent(1.0),
            font=self.game.fonts.heading(),
        )
        description_text = (
            f"Select a token for {self.player} by clicking one of the options below."
        )
        self.description = TextObject(
            self.game,
            lambda: description_text,
            Container.AutoPlacement(5),
            break_line_at=Percent(1.0),
        )
        self.token_selection_buttons = TokenSelectionButtons(
            self.game,
            self.page,
            self,
            PointSpecifier(
                CenterAlignedToObject(self, self.width),
                BelowObject(self.description, 5),
                self_corner=Corner.TOP_RIGHT,
            ),
            self.on_token_selection,
        )
        self.add_children(self.heading, self.description, self.token_selection_buttons)
        self.events.on(GameEvent.TOKEN_SELECTED, self.on_token_selection)


class HintText(TextObject):
    """Displays a hint to the right of the sidebar prompting the user to select a player"""

    def __init__(self, game: Monopoly, page: TokenSelection):
        super().__init__(
            game,
            self.get_content,
            page.get_main_pane_start_point(),
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


class TokenSelection(Page["Monopoly"]):
    def __init__(self, game: Monopoly) -> None:
        super().__init__(game, "Choose tokens")
        self.page_header = Header(game)
        self.player_list = PlayerList(game, self)
        self.hint_text = HintText(game, self)
        self.token_selection_pane: TokenSelectionPane | None = None
        self.add_objects(self.page_header, self.player_list, self.hint_text)

    def get_main_pane_start_point(self) -> PointSpecifier:
        x = RightOfObject(self.player_list, 10)
        assert self.page_header
        y = BelowObject(self.page_header, 10)

        return PointSpecifier(x, y)

    def show_token_selection_pane(self, player: Player):
        if self.token_selection_pane:
            print(f"Removing {self.token_selection_pane}")
            self.remove_object(self.token_selection_pane)
            self.token_selection_pane = None
        if self.hint_text:
            self.remove_object(self.hint_text)
            self.hint_text = None
        self.token_selection_pane = TokenSelectionPane(self.game, self, player)
        self.add_objects(self.token_selection_pane)
