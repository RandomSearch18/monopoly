import pygame
from game_engine import Game, Page, Theme
from pages.title_screen import TitleScreen

from pygame import Color
from pygame.font import Font

pygame.init()


class MonopolyTheme(Theme):
    # TODO Create color palette based on the Monopoly colors
    FOREGROUND = Color("black")
    BACKGROUND = Color("white")
    TITLE = Font(None, 64)


class Monopoly(Game):
    def __init__(self):
        super().__init__(60, MonopolyTheme(), "Monopoly", (800, 600))
        self.title_screen = TitleScreen(self)

    def get_initial_page(self):
        return self.title_screen


if __name__ == "__main__":
    game = Monopoly()
    game.game_session()
