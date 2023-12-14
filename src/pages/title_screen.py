from __future__ import annotations
from typing import Callable, Tuple

from pygame import Color
from game_engine import (
    CENTER,
    START,
    BelowObject,
    Corner,
    Game,
    GameObject,
    Page,
    Percent,
    PercentagePoint,
    Pixels,
    PointSpecifier,
    PointSpecifier,
    TextTexture,
)

from pygame.font import Font


class TitleText(GameObject):
    def get_content(self):
        return self.game.title

    def spawn_point(self) -> PointSpecifier:
        return PointSpecifier(Percent(0.50, position=CENTER), Pixels(5, position=START))

    def __init__(self, game: Game) -> None:
        self.game = game
        super().__init__(
            texture=TextTexture(game, self.get_content, self.game.fonts.title())
        )


class TitleText2(GameObject):
    def get_content(self):
        return "Game other title"

    def spawn_point(self) -> PointSpecifier:
        return self.spawn_at

    def __init__(self, game: Game, spawn_at: PointSpecifier) -> None:
        self.game = game
        self.spawn_at = spawn_at
        super().__init__(
            texture=TextTexture(game, self.get_content, self.game.fonts.title())
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
    def __init__(self, game: Game, label: str, font: Font | None = None):
        self.game = game
        self.label = label
        self.font = font or self.game.fonts.button()
        self.texture = ButtonTexture(
            game, self, self.get_content, self.font, Color("green")
        )
        super().__init__(self.texture)

    def get_content(self):
        return self.label

    def spawn_point(self) -> PointSpecifier:
        return PercentagePoint(0.5, 0.75)


class TitleScreen(Page):
    def __init__(self, game: Game) -> None:
        super().__init__(game, "Title screen")
        self.title_text = TitleText(game)

        self.objects.extend(
            [
                self.title_text,
                TitleText2(
                    game,
                    PointSpecifier(
                        Percent(0.5, position=CENTER), BelowObject(self.title_text, 5)
                    ),
                ),
                Button(game, "Start"),
            ]
        )
