from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Tuple

from pygame import Color
from pygame.font import Font
from events import GameEvent
from game_engine import (
    CENTER,
    START,
    Alignment2D,
    BelowObject,
    CenterAlignedToObject,
    CoordinateSpecifier,
    Corner,
    GameObject,
    PercentagePoint,
    Pixels,
    PixelsPoint,
    PlainColorTexture,
    PointSpecifier,
    PointSpecifier,
    TextTexture,
)

if TYPE_CHECKING:
    from main import Monopoly


class Container(GameObject["Monopoly"]):
    """Used for easy placement of multiple objects in a single row/column"""

    class AutoPlacement(PointSpecifier):
        def __init__(self, gap_pixels=0):
            self.gap_pixels = gap_pixels

    def __init__(
        self,
        game: Monopoly,
        spawn_at: PointSpecifier,
        get_size: Callable[[], Tuple[float, float]],
        color: Color | None = None,
        padding_top: float = 0,
    ) -> None:
        # self.game = game
        self._children: list[GameObject] = []
        texture = PlainColorTexture(game, color, get_size)
        self.spawn_at = spawn_at
        super().__init__(game, texture)
        self.tick_tasks.append(self.run_child_tick_tasks)
        self.padding_top = padding_top

        self.events.on(GameEvent.BEFORE_SPAWN, self.spawn_children)
        self.events.on(GameEvent.OBJECT_REMOVE, self.remove_all_children)

    def spawn_point(self) -> PointSpecifier:
        return self.spawn_at

    def draw(self):
        super().draw()
        for child in self._children:
            # If it wants to be automatically positioned, then work out where it should go (and store that)
            self.resolve_auto_placement(child)
            child.draw()

    def get_previous_auto_positioned_child(
        self, current_child: GameObject
    ) -> GameObject | None:
        """Returns the previous child that was auto-positioned, or None if there is none"""
        children = self.list_children()
        index = children.index(current_child)
        for child in reversed(children[:index]):
            # The child must have been auto-positioned and must still be in the UI
            if isinstance(child.spawn_point(), self.AutoPlacement) and child.exists:
                return child
        return None

    def resolve_auto_placement(self, object: GameObject):
        auto_placement = object.position()
        if not isinstance(auto_placement, self.AutoPlacement):
            return object
        previous_object = self.get_previous_auto_positioned_child(object)

        def spawn_below_previous_object() -> PointSpecifier:
            # Align the object to the middle of the container along the cross-axis (x-axis)
            x_spawn_point = CenterAlignedToObject(self, self.width)
            print(
                f"Container: Placing {object} {auto_placement.gap_pixels}px below {previous_object}"
            )
            y_spawn_point = (
                BelowObject(previous_object, auto_placement.gap_pixels)
                if previous_object
                else self.get_content_start_point()[1].to_moved(
                    auto_placement.gap_pixels
                )
            )
            return PointSpecifier(
                x_spawn_point, y_spawn_point, self_corner=Corner.TOP_LEFT
            )

        def resolve_auto_placement_again():
            # Marks the object as needing its auto-placement resolved
            print(f"Container: Re-resolving auto placement for {object}")
            object.set_position(object.spawn_point())
            object.events.remove_listener(GameEvent.OBJECT_REMOVE, event_listener)
            self.resolve_auto_placement(object)

        if previous_object:
            # Re-resolve the auto placement for this object if its designated previous object is removed
            event_listener = previous_object.events.on(
                GameEvent.OBJECT_REMOVE, resolve_auto_placement_again
            )

        object.set_position(spawn_below_previous_object())

    def get_content_start_point(
        self,
    ) -> tuple[CoordinateSpecifier, CoordinateSpecifier]:
        return self.spawn_at.x, self.spawn_at.y.to_moved(self.padding_top)

    def add_children(self, *objects: GameObject):
        for object in objects:
            if object in self._children:
                raise RuntimeError(f"{object} is already a child of {self}")
            object.parent = self
        self._children.extend(objects)
        if self.exists:
            self.game.all_objects.extend(objects)

    def spawn_children(self):
        assert self.exists, "Children should only be spawned once the container exists"
        for child in self._children:
            child.mark_as_spawned()
        self.game.all_objects.extend(self._children)

    def remove_all_children(self):
        for child in self._children:
            child.exists = False
            child.events.emit(GameEvent.OBJECT_REMOVE)
            self.game.all_objects.remove(child)
        self._children.clear()

    def list_children(self):
        return self._children.copy()

    def remove_child(self, child: GameObject):
        child.exists = False
        child.events.emit(GameEvent.OBJECT_REMOVE)
        self._children.remove(child)
        self.game.all_objects.remove(child)

    def run_child_tick_tasks(self):
        for child in self._children:
            child.run_tick_tasks()

    def get_widest_child(self) -> GameObject | None:
        """Find the child with the greatest total width, or None if there are no children"""
        widest_child = None
        for child in self._children:
            if widest_child is None or child.width() > widest_child.width():
                widest_child = child
        return widest_child

    def get_tallest_child(self) -> GameObject | None:
        tallest_child = None
        for child in self._children:
            if tallest_child is None or child.height() > tallest_child.height():
                tallest_child = child
        return tallest_child

    # def calculate_content_size(self) -> tuple[float, float]:
    #     widest_child = self.get_widest_child()
    #     tallest_child = self.get_tallest_child()
    #     if tallest_child is None or widest_child is None:
    #         return (0, 0)
    #     return (widest_child.width(), tallest_child.height())


class Header(Container):
    def __init__(self, game: Monopoly, page_title: str | None = None) -> None:
        HEADER_HEIGHT = 40
        align_to_middle = Pixels(HEADER_HEIGHT / 2, position=CENTER)
        spawn_at = PercentagePoint(0, 0, self_corner=Alignment2D.TOP_LEFT)
        super().__init__(
            game,
            spawn_at,
            lambda: (game.width(), HEADER_HEIGHT),
            game.theme.HEADER_BACKGROUND,
        )
        self.override_page_title = page_title

        # PAGE TITLE
        page_title_position = PointSpecifier(
            Pixels(5, position=START), align_to_middle, self_corner=Corner.TOP_LEFT
        )
        self.page_title_object = TextObject(
            game,
            self.get_title_text,
            page_title_position,
            color=game.theme.HEADER_FOREGROUND,
            font=game.fonts.system_font(2.5),
        )
        self.add_children(self.page_title_object)

    def get_title_text(self) -> str:
        if self.override_page_title:
            return self.override_page_title
        active_page = self.game.active_page
        if active_page:
            return active_page.title
        return "Loading"


class TextObject(GameObject["Monopoly"]):
    def spawn_point(self) -> PointSpecifier:
        return self.spawn_at

    def __init__(
        self,
        game: Monopoly,
        get_content: Callable[[], str],
        spawn_at: PointSpecifier,
        break_line_at: CoordinateSpecifier | None = None,
        font: Font | None = None,
        color: Color | None = None,
        padding: tuple[float, float] = (0, 0),
    ) -> None:
        self.game = game
        self.spawn_at = spawn_at
        font = font or game.fonts.body()
        super().__init__(
            game=game,
            texture=TextTexture(game, get_content, font, break_line_at, color, padding),
        )


class ButtonTexture(TextTexture):
    def __init__(
        self,
        game: Monopoly,
        object: Button,
        get_content: Callable[[], str | Tuple[str, Color]],
        font: Font,
        base_color: Color,
        border_radius: float,
        is_enabled: Callable[[], bool],
    ):
        super().__init__(game, get_content, font, border_radius=border_radius)
        self.button = object
        self.base_color = base_color
        self.is_enabled = is_enabled

    def get_background_color(self) -> Color | None:
        # Lighten the color if the button is hovered or pressed
        hover_color = self.base_color.lerp("white", 0.4)
        pressed_color = self.base_color.lerp("white", 0.6)
        self.opacity = 1
        if not self.is_enabled():
            # Apply 30% opacity if the button is disabled
            self.opacity = 0.3
            return self.base_color
        if self.button.is_pressed():
            return pressed_color
        if self.button.is_hover():
            return hover_color
        return self.base_color

    def get_padding(self) -> Tuple[float, float]:
        return (20, 10)

    def draw_at(self, provided_position: PointSpecifier):
        position_x, position_y = provided_position.calculate_top_left(
            self.game, self.width(), self.height()
        )
        padding_x, padding_y = self.get_padding()
        # Ensure that the top-left coordinate is the top-left of the padding, not the text
        position_x += padding_x
        position_y += padding_y
        super().draw_at(PixelsPoint(position_x, position_y))


class Button(GameObject):
    def __init__(
        self,
        game: Monopoly,
        label: str,
        callback: Callable,
        spawn_at: PointSpecifier,
        font: Font | None = None,
        border_radius: float = 5,
        is_enabled: Callable[[], bool] = lambda: True,
    ):
        # self.game = game
        self.label = label
        self.callback = callback
        self._spawn_at = spawn_at
        self.font = font or game.fonts.button()
        self.is_enabled = is_enabled
        self.border_radius = border_radius
        self.texture = ButtonTexture(
            game,
            self,
            self.get_content,
            self.font,
            Color("green"),
            self.border_radius,
            self.is_enabled,
        )
        super().__init__(game, self.texture)
        self.events.on(GameEvent.CLICK, self.run_callback)

    def run_callback(self, _):
        if not self.is_enabled():
            return
        self.callback()

    def get_content(self):
        return self.label

    def spawn_point(self) -> PointSpecifier:
        return self._spawn_at

    def __str__(self) -> str:
        return f"Button<'{self.label}'>"
