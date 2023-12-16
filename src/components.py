from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Tuple

from pygame import Color
from pygame.font import Font
from game_engine import (
    CENTER,
    START,
    Alignment2D,
    Corner,
    GameObject,
    PercentagePoint,
    Pixels,
    PlainColorTexture,
    PointSpecifier,
    PointSpecifier,
    TextTexture,
)

if TYPE_CHECKING:
    from main import Monopoly


class Container(GameObject["Monopoly"]):
    """Used for easy placement of multiple objects in a single row/column"""

    def __init__(
        self,
        game: Monopoly,
        spawn_at: PointSpecifier,
        size: tuple[float, float],
        color: Color | None = None,
    ) -> None:
        # self.game = game
        texture = PlainColorTexture(game, color, *size)
        self.spawn_at = spawn_at
        super().__init__(game, texture)
        self.children: list[GameObject] = []
        self.game  # (variable) game: T@__init__

    def spawn_point(self) -> PointSpecifier:
        return self.spawn_at

    def draw(self):
        super().draw()
        for child in self.children:
            child.draw()

    def add_child(self, object: GameObject):
        self.children.append(object)

    def add_children(self, *objects: GameObject):
        self.children.extend(objects)


class Header(Container):
    def __init__(self, game: Monopoly, page_title: str | None = None) -> None:
        HEADER_HEIGHT = 40
        align_to_middle = Pixels(HEADER_HEIGHT / 2, position=CENTER)
        spawn_at = PercentagePoint(0, 0, self_corner=Alignment2D.TOP_LEFT)
        super().__init__(
            game, spawn_at, (game.width(), HEADER_HEIGHT), game.theme.HEADER_BACKGROUND
        )
        self.override_page_title = page_title

        # PAGE TITLE
        page_title_position = PointSpecifier(
            Pixels(5, position=START), align_to_middle, self_corner=Corner.TOP_LEFT
        )
        self.page_title_object = Text(
            game,
            self.get_title_text,
            page_title_position,
            color=game.theme.HEADER_FOREGROUND,
            font=game.fonts.system_font(2.5),
        )
        self.add_child(self.page_title_object)

    def get_title_text(self) -> str:
        if self.override_page_title:
            return self.override_page_title
        active_page = self.game.active_page
        if active_page:
            return active_page.title
        return "Loading"


class Text(GameObject):
    def spawn_point(self) -> PointSpecifier:
        return self.spawn_at

    def __init__(
        self,
        game: Monopoly,
        get_content: Callable[[], str],
        spawn_at: PointSpecifier,
        font: Font | None = None,
        color: Color | None = None,
        padding: tuple[float, float] = (0, 0),
    ) -> None:
        self.spawn_at = spawn_at
        font = font or game.fonts.body()
        super().__init__(
            game=game,
            texture=TextTexture(game, get_content, font, color, padding),
        )


class ButtonTexture(TextTexture):
    def __init__(
        self,
        game: Monopoly,
        object: Button,
        get_content: Callable[[], str | Tuple[str, Color]],
        font: Font,
        base_color: Color,
    ):
        super().__init__(game, get_content, font)
        self.button = object
        self.base_color = base_color

    def get_background_color(self) -> Color | None:
        # Lighten the color if the button is hovered or pressed
        hover_color = self.base_color.lerp("white", 0.4)
        pressed_color = self.base_color.lerp("white", 0.6)
        if self.button.is_pressed():
            return pressed_color
        if self.button.is_hover():
            return hover_color
        return self.base_color

    def get_padding(self) -> Tuple[float, float]:
        return (20, 10)


class Button(GameObject):
    def __init__(
        self,
        game: Monopoly,
        label: str,
        callback: Callable,
        spawn_at: PointSpecifier,
        font: Font | None = None,
    ):
        # self.game = game
        self.label = label
        self.callback = callback
        self.spawn_at = spawn_at
        self.font = font or game.fonts.button()
        self.texture = ButtonTexture(
            game, self, self.get_content, self.font, Color("green")
        )
        super().__init__(game, self.texture)
        self.on_click_tasks.append(self.run_callback)

    def run_callback(self, _):
        self.callback()

    def get_content(self):
        return self.label

    def spawn_point(self) -> PointSpecifier:
        return self.spawn_at
