import pygame
from game_engine import Fonts, Game, Page, Theme
from pages.title_screen import TitleScreen
from pages.token_selection import TokenSelection

from pygame import Color
from pygame.font import Font

pygame.init()


class MonopolyTheme(Theme):
    # TODO Create color palette based on the Monopoly colors
    FOREGROUND = Color("black")
    BACKGROUND = Color("white")
    HEADER_BACKGROUND = Color("red")
    HEADER_FOREGROUND = Color("white")


class MonopolyFonts(Fonts):
    def base_font_size(self):
        return 16

    def size_miltiplier(self, multiplier: float) -> int:
        return int(self.base_font_size() * multiplier)

    def system_font(self, size_multiplier: float):
        return Font(None, self.size_miltiplier(size_multiplier))

    def title(self) -> Font:
        return self.system_font(4)

    def body(self) -> Font:
        return self.system_font(1)

    def button(self) -> Font:
        return self.system_font(2)


class Monopoly(Game):
    theme: MonopolyTheme

    def __init__(self):
        super().__init__(60, MonopolyTheme(), MonopolyFonts(), "Monopoly", (800, 600))
        self.title_screen = TitleScreen(self)
        self.token_selection = TokenSelection(self)

    def get_initial_page(self):
        return self.title_screen


if __name__ == "__main__":
    game = Monopoly()
    game.game_session()
