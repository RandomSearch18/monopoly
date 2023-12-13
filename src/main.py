from game_engine import Game, Theme

from pygame import Color


class MonopolyTheme(Theme):
    # TODO Create color palette based on the Monopoly colors
    FOREGROUND = Color("black")
    BACKGROUND = Color("white")


class Monopoly(Game):
    def __init__(self):
        super().__init__(60, MonopolyTheme(), "Monopoly", (800, 600))


if __name__ == "__main__":
    game = Monopoly()
    game.game_session()
