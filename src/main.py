from datetime import datetime
from pathlib import Path
import pygame
from data_storage import SavedGame
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
    fonts: MonopolyFonts

    def __init__(self):
        super().__init__(60, MonopolyTheme(), MonopolyFonts(), "Monopoly", (800, 600))
        self.title_screen = TitleScreen(self)
        self.token_selection = TokenSelection(self)
        self.current_game = None
        self.game_save_exception: Exception | None = None

    def get_initial_page(self):
        return self.title_screen

    def start_new_game(self):
        self.current_game = SavedGame(
            started_at=datetime.now(), players=[], is_saved_to_disk=False
        )
        self.save_current_game()
        print(f"Started new game: {self.current_game}")
        self.token_selection.activate()

    def save_current_game(self):
        current_game = self.current_game
        if not current_game:
            return
        serialized_game_data = current_game.model_dump_json(indent=2)
        json_file_name_timestamp = current_game.started_at.strftime("%Y-%m-%d %H-%M-%S")
        json_file_path = Path(
            "data",
            "saves",
            f"{json_file_name_timestamp}.json",
        )

        json_file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(json_file_path, "x") as json_file:
                json_file.write(serialized_game_data)
            current_game.is_saved_to_disk = True
        except OSError as exception:
            print(f"Error: Failed to save this game session: {exception}")
            self.game_save_exception = exception
            current_game.is_saved_to_disk = False


if __name__ == "__main__":
    game = Monopoly()
    game.game_session()
