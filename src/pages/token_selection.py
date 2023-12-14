from components import Text
from game_engine import START, Game, Page, Pixels, PointSpecifier


class TokenSelection(Page):
    def __init__(self, game: Game) -> None:
        super().__init__(game, "Selecting tokens")
        title_position = PointSpecifier(
            Pixels(5, position=START), Pixels(5, position=START)
        )
        self.page_title = Text(game, lambda: "Select a token", title_position)

        self.objects.extend([self.page_title])
