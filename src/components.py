from __future__ import annotations
from typing import Callable, Tuple

from pygame import Color
from game_engine import (
    Game,
    GameObject,
    PointSpecifier,
    PointSpecifier,
    TextTexture,
)


class Text(GameObject):
    def spawn_point(self) -> PointSpecifier:
        return self.spawn_at

    def __init__(
        self, game: Game, get_content: Callable[[], str], spawn_at: PointSpecifier
    ) -> None:
        self.game = game
        self.spawn_at = spawn_at
        super().__init__(
            texture=TextTexture(game, get_content, self.game.fonts.title())
        )


class ButtonTexture(TextTexture):
    def __init__(
        self,
        game: Game,
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
        return (50, 10)


class Button(GameObject):
    def __init__(
        self,
        game: Game,
        label: str,
        callback: Callable,
        spawn_at: PointSpecifier,
        font: Font | None = None,
    ):
        self.game = game
        self.label = label
        self.callback = callback
        self.spawn_at = spawn_at
        self.font = font or self.game.fonts.button()
        self.texture = ButtonTexture(
            game, self, self.get_content, self.font, Color("green")
        )
        super().__init__(self.texture)
        self.on_click_tasks.append(self.run_callback)

    def run_callback(self, _):
        self.callback()

    def get_content(self):
        return self.label

    def spawn_point(self) -> PointSpecifier:
        return self.spawn_at
