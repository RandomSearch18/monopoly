from game_engine import Game, Page, Theme

from pygame import Color


class MonopolyTheme(Theme):
    # TODO Create color palette based on the Monopoly colors
    FOREGROUND = Color("black")
    BACKGROUND = Color("white")


class Monopoly(Game):
    def __init__(self):
        self.title_screen = TitleScreen(self)
        super().__init__(60, MonopolyTheme(), "Monopoly", (800, 600))

    def get_initial_page(self):
        return self.title_screen


class TitleScreen(Page):
    def __init__(self, game: Game) -> None:
        super().__init__(game, "Title screen")


if __name__ == "__main__":
    game = Monopoly()
    game.game_session()
