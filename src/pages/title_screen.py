from __future__ import annotations
from typing import Callable, Tuple

from pygame import Color
from game_engine import (
    CENTER,
    START,
    Game,
    GameObject,
    Page,
    Percent,
    PercentagePoint,
    Pixels,
    PointSpecifier,
    PointSpecifier,
    TextTexture,
    Texture,
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
        return PercentagePoint(0.5, 0.5)

    def __init__(self, game: Game) -> None:
        self.game = game
        super().__init__(
            texture=TextTexture(game, self.get_content, self.game.fonts.title())
        )


class ButtonTexture(TextTexture):
    def __init__(
        self, game: Game, get_content: Callable[[], str | Tuple[str, Color]], font: Font
    ):
        super().__init__(game, get_content, font)

    def get_background_color(self) -> Color | None:
        return Color("green")


class Button(GameObject):
    def __init__(self, game: Game, label: str, font: Font | None = None):
        self.game = game
        self.label = label
        self.font = font or self.game.fonts.button()
        self.texture = ButtonTexture(game, self.get_content, self.font)
        super().__init__(self.texture)

    def get_content(self):
        return self.label

    def spawn_point(self) -> PointSpecifier:
        return PercentagePoint(0.5, 0.75)


class TitleScreen(Page):
    def __init__(self, game: Game) -> None:
        super().__init__(game, "Title screen")
        self.title_text = TitleText(game)

        self.objects.extend([self.title_text, TitleText2(game), Button(game, "Start")])
