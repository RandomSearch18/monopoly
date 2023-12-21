from datetime import datetime
from pathlib import Path
import pygame
from data_storage import Player, SavedGameData
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
    BACKGROUND_ACCENT = Color("#cfdccd")


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
        return self.system_font(1.75)

    def button(self) -> Font:
        return self.system_font(2)


class SavedGameManager:
    def __init__(self, session: Game, data: SavedGameData) -> None:
        self.game = session
        self.data = data
        self.game_save_exception: Exception | None = None
        self.save_file_exists = False

    def add_player(self, player: Player):
        self.data.players.append(player)
        self.save_to_disk()

    def save_to_disk(self):
        serialized_game_data = self.data.model_dump_json(indent=2)
        json_file_name_timestamp = self.data.started_at.strftime("%Y-%m-%d %H-%M-%S")
        json_file_path = Path(
            "data",
            "saves",
            f"{json_file_name_timestamp}.json",
        )

        if not self.save_file_exists:
            json_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Ensures that if we aren't expecting the file to already exist, we don't overwrite it
        mode = "w" if self.save_file_exists else "x"

        try:
            with open(json_file_path, mode) as json_file:
                json_file.write(serialized_game_data)
            self.save_file_exists = True
            self.data.is_saved_to_disk = True
            print("Successfuly saved game to disk")
        except OSError as exception:
            if isinstance(exception, FileExistsError):
                error_message = f"Attempted to write new save to {json_file_path}, but it already exists"
                raise RuntimeError(error_message)

            print(f"Error: Failed to save this game session: {exception}")
            self.game_save_exception = exception
            self.data.is_saved_to_disk = False


class Monopoly(Game):
    theme: MonopolyTheme
    fonts: MonopolyFonts

    def __init__(self):
        self.current_game = None
        super().__init__(60, MonopolyTheme(), MonopolyFonts(), "Monopoly", (800, 600))
        self.title_screen = TitleScreen(self)
        self.token_selection = TokenSelection(self)

    def get_initial_page(self):
        return self.title_screen

    def start_new_game(self):
        new_game = SavedGameData(
            started_at=datetime.now(), players=[], is_saved_to_disk=False
        )
        self.current_game = SavedGameManager(self, new_game)
        print(f"Started new game: {self.current_game}")
        self.token_selection.activate()


if __name__ == "__main__":
    game = Monopoly()
    game.game_session()
