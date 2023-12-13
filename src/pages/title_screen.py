from __future__ import annotations
from game_engine import (
    Game,
    GameObject,
    Page,
    PercentagePoint,
    Pixels,
    PixelsPoint,
    PointSpecifier,
    TextTexture,
)


class TitleText(GameObject):
    def get_content(self):
        return self.game.title

    def spawn_point(self) -> PointSpecifier:
        return PixelsPoint(Pixels(400, measure_to=0), Pixels(5, measure_to=0))

    def __init__(self, game: Game) -> None:
        self.game = game
        super().__init__(
            texture=TextTexture(game, self.get_content, self.game.theme.TITLE)
        )

    def draw(self):
        return self.texture.draw_at(self.position)


class TitleScreen(Page):
    def __init__(self, game: Game) -> None:
        super().__init__(game, "Title screen")
        self.title_text = TitleText(game)

        self.objects.extend([self.title_text])
