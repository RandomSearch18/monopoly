from __future__ import annotations
import copy
import math
from collections import deque
from enum import Enum
import re

from typing import Callable, Generic, Literal, Optional, Tuple, TypeVar
import pygame
from pygame import Color, Surface
from pygame.rect import Rect
from pygame.event import Event
from pygame.font import Font

from events import EventEmitter, GameEvent


class Corner(Enum):
    TOP_LEFT = (-1, -1)
    TOP_RIGHT = (1, -1)
    BOTTOM_LEFT = (-1, 1)
    BOTTOM_RIGHT = (1, 1)


class Alignment2D(Enum):
    TOP_LEFT = (-1, -1)
    TOP_RIGHT = (1, -1)
    BOTTOM_LEFT = (-1, 1)
    BOTTOM_RIGHT = (1, 1)
    CENTER = (0, 0)


class Edge(Enum):
    TOP = (0, -1)
    BOTTOM = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)


START = -1
CENTER = 0
END = 1
# Represents one of the two "ends" of a line, or its center.
# -1 is the start of the line, 0 is the center, and 1 is the end of the line
LineEdge = Literal[-1, 0, 1]


class CoordinateSpecifier:
    """A specifier for a single coordinate value (either x or y)"""

    # 0 would mean the top or left edge of the window (greater pixels value moves right/down);
    # whereas 1 would mean the bottom or right edge of the window (greater pixels value moves left/up)
    outer_edge: Literal[-1, 1]
    # If the coordinate is part of an object/line, this is the edge of the object/line that the coordinate represents
    # On a line, -1 is the start of the line, 0 is the center, and 1 is the end of the line
    # In an object, -1 is the left/top edge, 0 is the center, and 1 is the right/bottom edge
    self_edge: LineEdge | None
    # Stores a postive or negative number of pixels that the resolved value should be "moved" by
    move_by_pixels: float = 0

    def _apply_movement(self, resolved_coordinate) -> float:
        return resolved_coordinate + self.move_by_pixels

    def resolve_unmoved_value(self, outer_size: float) -> float:
        raise NotImplementedError()

    def resolve(self, outer_size: float) -> float:
        return self._apply_movement(self.resolve_unmoved_value(outer_size))

    def move_by(self, pixels: float):
        self.move_by_pixels += pixels

    def copy(self):
        return copy.copy(self)

    def to_moved(self, pixels: float):
        new_specifier = self.copy()
        new_specifier.move_by(pixels)
        return new_specifier

    def calculate_offest_to_edge(
        self, target_edge: LineEdge, line_length: float
    ) -> float:
        if target_edge == self.self_edge:
            return 0

        if self.self_edge == 0:
            # Calculating from center
            absolute_offset = line_length / 2
            multiplier = target_edge
            return absolute_offset * multiplier

        # Calculating from an edge
        absolute_offset = line_length
        return -absolute_offset if self.outer_edge == 1 else +absolute_offset

    def find_edge(self, edge: LineEdge, outer_size: float, self_length: float) -> float:
        raise NotImplementedError()


class Pixels(CoordinateSpecifier):
    def __init__(
        self,
        pixels: float,
        outer_edge: Literal[-1, 1] = -1,
        position: LineEdge | None = None,
    ) -> None:
        self.pixels = pixels
        self.outer_edge = outer_edge  # Outer reference point
        self.self_edge = position  # Inner reference point

    def move_by(self, pixels: float):
        pixel_movement = -pixels if self.outer_edge == 1 else +pixels
        self.pixels += pixel_movement

    def resolve_unmoved_value(self, outer_size: float) -> float:
        start_from = outer_size if self.outer_edge == 1 else 0
        offset = -self.pixels if self.outer_edge == 1 else +self.pixels
        actual_coordinate = start_from + offset
        return actual_coordinate

    def find_edge(self, edge: LineEdge, outer_size: float, self_length: float) -> float:
        coordinate_value = self.resolve(outer_size)
        if self.self_edge is None:
            raise RuntimeError("Cannot find edge of a standalone coordinate")
        offset = self.calculate_offest_to_edge(edge, self_length)
        return coordinate_value + offset


class Percent(CoordinateSpecifier):
    def __init__(
        self,
        percent: float,
        outer_edge: Literal[-1, 1] = -1,
        position: LineEdge | None = None,
    ) -> None:
        self.percent = percent
        self.outer_edge = outer_edge  # Outer reference point
        self.self_edge = position  # Inner reference point

    def resolve_unmoved_value(self, outer_size: float) -> float:
        pixels_specifier = Pixels(
            self.percent * outer_size, self.outer_edge, self.self_edge
        )
        return pixels_specifier.resolve(outer_size)

    def calculate_offest_to_edge(self, target_edge: LineEdge, line_length: float):
        pixels_specifier = Pixels(
            self.percent * line_length, self.outer_edge, self.self_edge
        )
        return pixels_specifier.calculate_offest_to_edge(target_edge, line_length)

    def find_edge(self, edge: LineEdge, outer_size: float, self_length: float) -> float:
        pixels_specifier = Pixels(
            self.percent * outer_size, self.outer_edge, self.self_edge
        )
        return pixels_specifier.find_edge(edge, outer_size, self_length)


class BelowObject(CoordinateSpecifier):
    def __init__(self, leader_object: GameObject, gap_pixels: float = 0) -> None:
        self.leader_object = leader_object
        self.gap_pixels = gap_pixels
        self.self_edge = START
        print(f"Specified point {gap_pixels}px below {leader_object}")

    def resolve_unmoved_value(self, outer_size: float) -> float:
        leader_position = self.leader_object.current_coordinates
        if not leader_position:
            raise RuntimeError(
                f"Can't render an object relative to an object that hasn't been rendered yet ({self.leader_object})!"
            )
        leader_bottom = leader_position[1] + self.leader_object.height()
        # print(self.gap_pixels)
        return leader_bottom + self.gap_pixels

    def find_edge(self, edge: LineEdge, outer_size: float, self_length: float) -> float:
        coordinate_value = self.resolve(outer_size)
        offset = self.calculate_offest_to_edge(edge, self_length)
        return coordinate_value + offset


class BelowPoint(CoordinateSpecifier):
    def __init__(
        self, leader_point: Callable[[], Tuple[float, float]], gap_pixels=0.0
    ) -> None:
        self.leader_point = leader_point
        self.gap_pixels = gap_pixels
        self.self_edge = START

    def resolve_leader_point(self) -> Tuple[float, float]:
        leader_point = self.leader_point()
        return leader_point

    def resolve_unmoved_value(self, outer_size: float) -> float:
        leader_position = self.resolve_leader_point()
        _, leader_y = leader_position
        return leader_y + self.gap_pixels

    def find_edge(self, edge: LineEdge, outer_size: float, self_length: float) -> float:
        coordinate_value = self.resolve(outer_size)
        offset = self.calculate_offest_to_edge(edge, self_length)
        return coordinate_value + offset


class RightOfObject(CoordinateSpecifier):
    def __init__(self, leader_object: GameObject, gap_pixels: float) -> None:
        self.leader_object = leader_object
        self.gap_pixels = gap_pixels
        self.self_edge = START

    def resolve_unmoved_value(self, outer_size: float) -> float:
        leader_position = self.leader_object.current_coordinates
        if not leader_position:
            raise RuntimeError(
                f"Can't render an object relative to an object that hasn't been rendered yet ({self.leader_object})!"
            )
        leader_position_x, _ = leader_position
        leader_right = leader_position_x + self.leader_object.width()
        return leader_right + self.gap_pixels

    def find_edge(self, edge: LineEdge, outer_size: float, self_length: float) -> float:
        coordinate_value = self.resolve(outer_size)
        offset = self.calculate_offest_to_edge(edge, self_length)
        return coordinate_value + offset


class CenterAlignedToObject(CoordinateSpecifier):
    def __init__(
        self, leader_object: GameObject, get_leader_object_length: Callable[[], float]
    ) -> None:
        self.leader_object = leader_object
        # This should be set to te width or height of the leader_object, depending on which axis is being used
        self.get_leader_object_length = get_leader_object_length
        self.self_edge = CENTER

    def resolve_unmoved_value(self, _=None) -> float:
        leader_position = self.leader_object.current_coordinates
        if not leader_position:
            raise RuntimeError(
                f"Can't render an object relative to an object that hasn't been rendered yet ({self.leader_object})!"
            )
        leader_center = leader_position[0] + self.get_leader_object_length() / 2
        return leader_center

    def find_edge(self, edge: LineEdge, _outer_size, self_length: float) -> float:
        resolved_coordinate = self.resolve_unmoved_value()
        offset = self.calculate_offest_to_edge(edge, self_length)
        return resolved_coordinate + offset


class PointSpecifier:
    def __init__(
        self,
        x: CoordinateSpecifier,
        y: CoordinateSpecifier,
        outer_corner: Corner = Corner.TOP_LEFT,
        self_corner: Optional[Corner] = None,
    ):
        self.x = x
        self.y = y
        self.outer_corner = outer_corner
        self.self_corner = self_corner

    def resolve(self, game: Game) -> Tuple[float, float]:
        resolved_x_coordinate = self.x.resolve(game.width())
        resolved_y_coordinate = self.y.resolve(game.height())
        return (resolved_x_coordinate, resolved_y_coordinate)

    def on_window_resize(self, event: Event):
        """Responds to a window resize event to keep the position within window bounds"""
        pass

    def calculate_top_left(self, game: Game, object_width: float, object_height: float):
        return self.find_corner(Corner.TOP_LEFT, game, object_width, object_height)

    def find_corner(
        self, corner: Corner, game: Game, object_width: float, object_height: float
    ):
        corner_x, corner_y = corner.value
        target_corner_x = self.x.find_edge(corner_x, game.width(), object_width)
        target_corner_y = self.y.find_edge(corner_y, game.height(), object_height)
        return (target_corner_x, target_corner_y)


class PercentagePoint(PointSpecifier):
    def __init__(
        self,
        x: float,
        y: float,
        outer_corner: Corner = Corner.TOP_LEFT,
        self_corner: Optional[Alignment2D] = Alignment2D.CENTER,
    ):
        outer_corner_x, outer_corner_y = outer_corner.value
        self_corner_x, self_corner_y = (
            self_corner.value if self_corner else (None, None)
        )
        super().__init__(
            x=Percent(x, outer_corner_x, self_corner_x),
            y=Percent(y, outer_corner_y, self_corner_y),
        )


class PixelsPoint(PointSpecifier):
    def __init__(self, x_pixels: float, y_pixels: float):
        super().__init__(
            Pixels(x_pixels, position=START),
            Pixels(y_pixels, position=START),
            self_corner=Corner.TOP_LEFT,
        )


class Box:
    def __init__(self, x1: float, y1: float, x2: float, y2: float):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def top(self) -> float:
        return self.y1

    @property
    def bottom(self) -> float:
        return self.y2

    @property
    def left(self) -> float:
        return self.x1

    @property
    def right(self) -> float:
        return self.x2

    def enlarge_by_x(self, pixels: float):
        """Enlarges the box by the provided number of pixels on the left and the right"""
        self.x1 -= pixels
        self.x2 += pixels

    def enlarge_by_y(self, pixels: float):
        """Enlarges the box by the provided number of pixels on the top and the bottom"""
        self.y1 -= pixels
        self.y2 += pixels

    def center(self) -> Tuple[float, float]:
        """Calculates the coordinates of the center of the box"""
        center_x = self.left + self.width / 2
        center_y = self.top + self.height / 2

        return (center_x, center_y)

    def is_inside(self, outer_box: Box, allowed_margin=0.0) -> bool:
        is_within_x = (
            outer_box.left - self.left <= allowed_margin
            and self.right - outer_box.right <= allowed_margin
        )

        is_within_y = (
            outer_box.top - self.top <= allowed_margin
            and self.bottom - outer_box.bottom <= allowed_margin
        )

        return is_within_x and is_within_y

    def intersects_with_point(self, coordinates: Tuple[float, float]):
        other_x, other_y = coordinates
        is_within_x = self.x1 <= other_x <= self.x2
        is_within_y = self.y1 <= other_y <= self.y2
        return is_within_x and is_within_y

    def is_outside(self, other_box: Box) -> bool:
        is_outside_x = self.right < other_box.left or self.left > other_box.right

        is_outside_y = self.bottom < other_box.top or self.top > other_box.bottom

        return is_outside_x or is_outside_y

    def to_rect(self) -> Rect:
        return Rect(self.left, self.top, self.width, self.height)

    def __str__(self) -> str:
        return f"Box<({self.x1}, {self.y1}) ({self.x2}, {self.y2})>"

    @staticmethod
    def from_rect(rect: Rect):
        return Box(x1=rect.left, y1=rect.top, x2=rect.right, y2=rect.bottom)


class Theme:
    """Colors and fonts used by the game, labeled according to their purpose"""

    FOREGROUND: Color
    BACKGROUND: Color


class Fonts:
    def title(self) -> Font:
        raise NotImplementedError()

    def body(self) -> Font:
        raise NotImplementedError()

    def button(self) -> Font:
        raise NotImplementedError()


class Game:
    def __init__(
        self,
        max_fps,
        theme: Theme,
        fonts: Fonts,
        title: str,
        window_size: Tuple[int, int],
    ):
        # Window display config
        self.theme = theme
        self.fonts = fonts
        self.background_color = self.theme.BACKGROUND
        self.title = title

        # Initilise the display surface
        self.surface = pygame.display.set_mode(window_size, pygame.RESIZABLE)
        pygame.display.set_caption(title)

        # Initialise other game components
        self.max_fps = max_fps
        self.clock = pygame.time.Clock()
        self.exited = False
        self.top_level_objects: list[GameObject] = []
        self.all_objects: list[GameObject] = []
        self.old_window_dimensions = (self.width(), self.height())
        self.key_action_callbacks = {}
        self.key_up_callbacks = {}
        self.is_paused = False
        self.recent_frame_times = deque(maxlen=10)
        self.active_page: Page | None = None

        # Set up default keybinds
        self.keybinds = {}

        pygame.init()

    def add_objects(self, *objects: GameObject):
        self.all_objects.extend(objects)
        self.top_level_objects.extend(objects)

    def remove_object(self, object: GameObject):
        self.all_objects.remove(object)
        self.top_level_objects.remove(object)

    def get_initial_page(self) -> Page:
        raise NotImplementedError()

    def width(self) -> int:
        """Returns the width of the window, in pixels"""
        return self.surface.get_width()

    def height(self) -> int:
        """Returns the height of the window, in pixels"""
        return self.surface.get_height()

    def window_box(self) -> Box:
        """Calculates the box that represents the size of the window"""
        x1 = 0
        y1 = 0
        x2 = self.width()
        y2 = self.height()

        return Box(x1, y1, x2, y2)

    def set_window_title(self, title_part: str):
        pygame.display.set_caption(f"{title_part} - {self.title}")

    def all_rendered_objects(self) -> list[GameObject]:
        return [object for object in self.all_objects if object.exists]

    def on_event(self, event):
        # print(event)
        if event.type == pygame.QUIT:
            self.exited = True
        elif event.type == pygame.VIDEORESIZE:
            event.old_dimensions = self.old_window_dimensions
            for object in self.all_objects:
                object.position().on_window_resize(event)
            self.old_window_dimensions = (self.width(), self.height())

        # Keyboard input
        elif event.type == pygame.KEYDOWN:
            if event.key in self.keybinds:
                action = self.keybinds[event.key]
                self.trigger_key_action(action, event)
        elif event.type == pygame.KEYUP:
            if event.key in self.key_up_callbacks:
                callback = self.key_up_callbacks[event.key]
                callback()

        # Mouse clicks
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button != 1:
                # Only trigger for left clicks
                return
            for object in self.all_rendered_objects():
                if object.collision_box().intersects_with_point(event.pos):
                    # Fire the click event for the object
                    object.events.emit(GameEvent.CLICK, event)

    def trigger_key_action(self, action: str, event: pygame.event.Event):
        if action not in self.key_action_callbacks:
            return
        action_callback = self.key_action_callbacks[action]
        on_key_up = action_callback(event)
        self.key_up_callbacks[event.key] = lambda: on_key_up(event)

    def on_key_action(self, action: str):
        def decorator(callback):
            self.key_action_callbacks[action] = callback

        return decorator

    def milliseconds_per_frame(self):
        """Returns average time taken to compute, render, and draw the last 10 frames"""
        times = self.recent_frame_times
        if not len(times):
            # Default to 0 if we haven't recorded any frame times yet
            return 0
        sum = 0
        for time in times:
            sum += time
        average = sum / len(times)
        return average

    def execute_tick(self):
        """Updates the states and positions of all game objects.

        - One tick should happen every frame
        - Runs the event handlers for any events emitted since the last tick
        - Runs the tick tasks for each game object
        - This is essentially the computational/"logical server" side of the game
        """
        for event in pygame.event.get():
            self.on_event(event)

        # Update each top-level object
        if not self.is_paused:
            for object in self.top_level_objects:
                object.run_tick_tasks()

    def draw_frame(self):
        """Redraws the screen, ready for the display to be refreshed

        - This should happen every frame
        - Should be called after objects have ticked but before the display is updated
        - This is the graphical/"logical client" side of the game
        """
        # Clear the entire surface
        self.surface.fill(self.background_color)

        # Draw each top-level object
        for object in self.top_level_objects:
            object.draw()

    def update_display(self):
        pygame.display.update()

    def initialise_game_session(self):
        pass

    def game_session(self):
        self.initialise_game_session()
        self.get_initial_page().activate()

        while not self.exited:
            self.execute_tick()
            self.draw_frame()
            self.update_display()

            self.recent_frame_times.append(self.clock.get_rawtime())
            self.clock.tick(self.max_fps)

        self.top_level_objects.clear()
        self.key_action_callbacks.clear()
        self.key_up_callbacks.clear()


T = TypeVar("T", bound=Game)


class Page(Generic[T]):
    """A page is a self-contained view containing its own set of objects"""

    def __init__(self, game: T, title: str) -> None:
        self.game = game
        self._objects: list[GameObject[T]] = []
        self.title = title
        self.page_header: GameObject[T] | None = None

    def activate(self):
        if self.title:
            self.game.set_window_title(self.title)
        self.game.active_page = self
        # Replace active game objects with our objects:
        self.game.all_objects.clear()
        self.game.top_level_objects.clear()
        self.game.add_objects(*self._objects)

    def add_objects(self, *objects: GameObject[T]):
        self._objects.extend(objects)
        self.game.add_objects(*objects)

    def remove_object(self, object: GameObject[T]):
        object.exists = False
        object.events.emit(GameEvent.OBJECT_REMOVE)
        self._objects.remove(object)
        self.game.remove_object(object)

    def get_content_start_point(
        self,
    ) -> PointSpecifier:
        if not self.page_header:
            return PointSpecifier(Pixels(0, position=START), Pixels(0, position=START))

        return PointSpecifier(Pixels(0, position=START), BelowObject(self.page_header))

    def get_content_height(self) -> float:
        page_header = self.page_header
        if not page_header:
            return self.game.height()
        return self.game.height() - page_header.height()

    def get_content_width(self) -> float:
        return self.game.width()


class Texture:
    def __init__(self):
        pass

    def height(self) -> float:
        raise NotImplementedError()

    def width(self) -> float:
        raise NotImplementedError()

    def draw_at(self, position: PointSpecifier):
        pass


class PlainColorTexture(Texture):
    def __init__(
        self,
        game: Game,
        color: Color | None,
        get_size: Callable[[], Tuple[float, float]],
    ):
        self.game = game
        self.color = color
        self.get_size = get_size

    def width(self) -> float:
        return self.get_size()[0]

    def height(self) -> float:
        return self.get_size()[1]

    def draw_at(self, position: PointSpecifier):
        if not self.color:
            return

        x1, y1 = position.calculate_top_left(self.game, self.width(), self.height())

        pygame.draw.rect(
            self.game.surface,
            self.color,
            Rect(x1, y1, self.width(), self.height()),
        )


class TextTexture(Texture):
    def width(self) -> float:
        return self.current_outer_box.width

    def height(self) -> float:
        return self.current_outer_box.height

    def inner_width(self) -> float:
        return self.current_text_rect.width

    def inner_height(self) -> float:
        return self.current_text_rect.height

    def get_content(self):
        provided_content = self._get_content()
        if isinstance(provided_content, str):
            default_color = self.default_color or self.game.theme.FOREGROUND
            return (provided_content, default_color)
        return provided_content

    def render_text_line(
        self,
        text_content: str,
        text_color: Color,
        start_x: float,
        start_y: float,
        padding: Tuple[float, float],
    ):
        """Computes a surface and bounding box for a line of, but doesn't draw it to the screen"""
        use_antialiasing = True
        text_surface = self.font.render(text_content, use_antialiasing, text_color)

        text_rect = text_surface.get_rect()
        text_rect.left = math.floor(start_x)
        text_rect.top = math.floor(start_y)

        padding_x, padding_y = padding
        outer_box = Box.from_rect(text_rect)
        outer_box.enlarge_by_x(padding_x)
        outer_box.enlarge_by_y(padding_y)

        return text_surface, outer_box, text_rect

    def split_text(self, text: str, max_width: float, font: Font):
        """Splits the provides string into lines by applying word wrapping

        - Each line will be no longer than max_width
        - Uses pygame.font.Font.size() to determine how wide the text will be
        - Source: Written by GitHub Copilot
        """
        words = re.split(r"(\s+)", text)
        lines = []
        acceptable_line = ""  # A line that we can guarantee will fit
        current_line = ""  # The line that we use to test if it fits
        for word in words:
            if not current_line:
                current_line = word
                continue
            current_line += word
            text_width, _ = font.size(current_line)
            if text_width > max_width:
                # The current line is too long, so use the acceptable_line from last iteration
                lines.append(acceptable_line.lstrip())
                current_line = word
            else:
                # The current line fits
                acceptable_line = current_line
        if current_line:
            # Add the final line
            lines.append(current_line.lstrip())
        return lines

    def render_wrapped_text(
        self, top_left: Tuple[float, float], padding: Tuple[float, float]
    ) -> tuple[Surface, Box, Rect]:
        start_x, start_y = top_left
        text_content, text_color = self.get_content()
        if not self.break_line_at:
            return self.render_text_line(
                text_content, text_color, start_x, start_y, padding
            )
        break_at_x = self.break_line_at.resolve(self.game.width())
        max_width = break_at_x - start_x

        lines = self.split_text(text_content, max_width, self.font)

        # Render each line
        rendered_lines: list[tuple[Surface, Box, Rect]] = []
        line_top = start_y
        for line in lines:
            surface, outer_box, text_rect = self.render_text_line(
                line, text_color, start_x, start_y, padding=(0, 0)
            )
            rendered_lines.append((surface, outer_box, text_rect))
            line_top += outer_box.height

        # Calculate the bounding box for the entire text block
        total_height = sum([box.height for _, box, _ in rendered_lines])
        total_width = max([box.width for _, box, _ in rendered_lines])

        # Create a surface for the text block
        # The SRCALPHA flag makes it use per-pixel transparency
        text_surface = Surface((total_width, total_height), pygame.SRCALPHA)

        # Draw each line onto the text surface
        current_line_top = 0
        for surface, outer_box, text_rect in rendered_lines:
            text_surface.blit(surface, (0, current_line_top))
            current_line_top += outer_box.height

        # Calculate the outer box for the text block (including padding)
        text_rect = text_surface.get_rect()
        text_rect.left = math.floor(start_x)
        text_rect.top = math.floor(start_y)
        padding_x, padding_y = padding
        outer_box = Box.from_rect(text_rect)
        outer_box.enlarge_by_x(padding_x)
        outer_box.enlarge_by_y(padding_y)

        return text_surface, outer_box, text_rect

    def get_dummy_bounding_boxes(self):
        text_content, text_color = self.get_content()
        _, outer_box, text_rect = self.render_text_line(
            text_content, text_color, 0, 0, self.get_padding()
        )
        return outer_box, text_rect

    def __init__(
        self,
        game: Game,
        get_content: Callable[[], str | Tuple[str, Color]],
        font: pygame.font.Font,
        break_line_at: CoordinateSpecifier | None = None,
        default_color: Color | None = None,
        padding: Tuple[float, float] = (0, 0),
    ):
        self.game = game
        self._get_content = get_content
        self.font = font
        self._padding = padding
        self.default_color = default_color
        self.break_line_at = break_line_at
        # Before first render, use bboxes that are the correct size but at an arbitrary position.
        # This is becuase we might need to use the bbox size to resolve its spawn position
        self.current_outer_box, self.current_text_rect = self.get_dummy_bounding_boxes()

    def get_background_color(self) -> Color | None:
        return None

    def get_padding(self) -> Tuple[float, float]:
        return self._padding

    def draw_at(self, position: PointSpecifier):
        top_left = position.calculate_top_left(
            self.game, self.inner_width(), self.inner_height()
        )
        padding = self.get_padding()
        text_surface, outer_box, text_rect = self.render_wrapped_text(top_left, padding)
        self.current_outer_box = outer_box
        self.current_text_rect = text_rect
        background = self.get_background_color()
        if background:
            pygame.draw.rect(self.game.surface, background, outer_box.to_rect())
        self.game.surface.blit(text_surface, text_rect)


class ImageTexture(Texture):
    def __init__(self, game, image):
        self.game = game
        self.image = image

    def draw_at(self, position: PointSpecifier):
        start_x, start_y = position.calculate_top_left(
            self.game, self.width(), self.height()
        )
        self.game.surface.blit(self.image, (start_x, start_y))


class GameObject(Generic[T]):
    def height(self) -> float:
        return self.texture.height()

    def width(self) -> float:
        return self.texture.width()

    def spawn_point(self) -> PointSpecifier:
        raise NotImplementedError()

    def set_position(self, position: PointSpecifier):
        self._position = position

    def position(self) -> PointSpecifier:
        return self._position

    def reset(self):
        """Moves the object to its initial position (spawn point)"""
        spawn_point = self.spawn_point()
        self.set_position(spawn_point)

    def __init__(
        self,
        game: T,
        texture: Texture,
        solid=True,
    ):
        # assert hasattr(self, "game")
        # assert isinstance(self.game, Game)
        self.game: T = game
        self.events = EventEmitter()
        self.tick_tasks: list[Callable] = []
        self.texture = texture
        self.is_solid = solid
        self.spawned_at = pygame.time.get_ticks()
        self.current_coordinates: Tuple[float, float] | None = None
        self.exists = False
        self.parent: GameObject | None = None
        self.reset()

    def draw(self):
        self.current_coordinates = self.position().calculate_top_left(
            self.game, self.width(), self.height()
        )
        self.exists = True
        # print(self, self.position.resolve(self.game))
        self.texture.draw_at(self.position())

    def run_tick_tasks(self):
        for callback in self.tick_tasks:
            callback()

    def age(self) -> float:
        """Returns milliseconds since this game object was initialised"""
        current_time = pygame.time.get_ticks()
        return current_time - self.spawned_at

    def calculate_center_bounds(self, parent_width: float, parent_height: float) -> Box:
        """Calculates the box of possible positions for the center point of this object"""
        x_padding = self.width() / 2
        y_padding = self.height() / 2

        x1 = 0 + x_padding
        x2 = parent_width - x_padding
        y1 = 0 + y_padding
        y2 = parent_height - y_padding

        return Box(x1, y1, x2, y2)

    def collision_box(self) -> Box:
        """Calculates the visual bounding box (i.e. collision box) for this object"""
        x1, y1 = self.position().calculate_top_left(
            self.game, self.width(), self.height()
        )
        x2 = x1 + self.width()
        y2 = y1 + self.height()

        return Box(x1, y1, x2, y2)

    def calculate_position_percentage(self, bounds: Box) -> Tuple[float, float]:
        """Calculates the position of the center of the object, returning coordinates in the form (x, y)

        - Coordinates are scaled from 0.0 to 1.0 to represent percentage relative to the provided bounding box
        """
        center_x, center_y = self.collision_box().center()

        # Calculate the percentage position of the center relative to the bounding box
        percentage_x = (center_x - bounds.left) / bounds.width
        percentage_y = (center_y - bounds.top) / bounds.height

        return percentage_x, percentage_y

    def map_relative_position_to_box(
        self,
        position_percentage: Tuple[float, float],
        new_center_point_bounds: Box,
    ) -> Tuple[float, float]:
        """Calculates the new center point based on the saved percentage and the new bounding box dimensions"""
        limit = new_center_point_bounds

        # Calculate the new center based on the percentage and the new bounding box
        new_center_x = limit.left + limit.width * position_percentage[0]
        new_center_y = limit.top + limit.height * position_percentage[1]

        return new_center_x, new_center_y

    def is_within_window(self, allowed_margin=0.0):
        window = self.game.window_box()
        return self.collision_box().is_inside(window, allowed_margin)

    def is_outside_window(self):
        window = self.game.window_box()
        return self.collision_box().is_outside(window)

    def coordinates(self):
        return self.position().resolve(self.game)

    def closest_window_edge(self) -> Edge:
        outer_box = self.game.window_box()
        our_x, our_y = self.coordinates()
        distances = {
            Edge.TOP: abs(outer_box.top - our_y),
            Edge.BOTTOM: abs(outer_box.bottom - our_y),
            Edge.LEFT: abs(outer_box.left - our_x),
            Edge.RIGHT: abs(outer_box.right - our_x),
        }
        closest_edge = min(distances, key=distances.get)  # type: ignore
        return closest_edge

    def is_hover(self) -> bool:
        """Returns True if the object's collision box is being hovered over by the mouse"""
        mouse_position = pygame.mouse.get_pos()
        return self.collision_box().intersects_with_point(mouse_position)

    def is_pressed(self) -> bool:
        """Returns True if the object's collision box is being clicked on"""
        left_mouse_is_down, _, _ = pygame.mouse.get_pressed()
        mouse_position = pygame.mouse.get_pos()
        mouse_is_within_object = self.collision_box().intersects_with_point(
            mouse_position
        )
        return mouse_is_within_object and left_mouse_is_down


# FIXME Maybe re-implement this if/when we need it
# class Velocity:
#     def on_tick(self):
#         x_movement = self.x
#         y_movement = self.y

#         self.object.position.move_right(x_movement)
#         self.object.position.move_down(y_movement)

#     def __init__(self, game_object: GameObject, base_speed: float):
#         # Magnitudes of velocity, measured in pixels/tick
#         self.x = 0
#         self.y = 0

#         # The speed that the object will travel at by default (pixels/tick)
#         self.base_speed = base_speed

#         self.object = game_object
#         self.object.tick_tasks.append(self.on_tick)

#     def shove_x(self, multiplier=1.0):
#         self.x = self.base_speed * multiplier

#     def shove_y(self, multiplier=1.0):
#         self.y = self.base_speed * multiplier
