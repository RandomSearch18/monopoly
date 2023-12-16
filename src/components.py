from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Tuple

from pygame import Color
from pygame.font import Font
from game_engine import (
    CENTER,
    START,
    Alignment2D,
    BelowObject,
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
        def __init__(self):
            pass

    def __init__(
        self,
        game: Monopoly,
        spawn_at: PointSpecifier,
        get_size: Callable[[], Tuple[float, float]],
        color: Color | None = None,
    ) -> None:
        # self.game = game
        self._children: list[GameObject] = []
        texture = PlainColorTexture(game, color, get_size)
        self.spawn_at = spawn_at
        super().__init__(game, texture)
        self.tick_tasks.append(self.run_child_tick_tasks)

    def spawn_point(self) -> PointSpecifier:
        return self.spawn_at

    def draw(self):
        super().draw()
        for child in self._children:
            # If it wants to be automatically positioned, then work out where it should go (and store that)
            child = self.resolve_auto_placement(child)
            child.draw()

    def get_previous_auto_positioned_child(
        self, current_child: GameObject
    ) -> GameObject | None:
        """Returns the previous child that was auto-positioned, or None if there is none"""
        index = self._children.index(current_child)
        for child in reversed(self._children[:index]):
            if isinstance(child.spawn_point(), self.AutoPlacement):
                return child
        return None

    def resolve_auto_placement(self, object: GameObject) -> GameObject:
        if not isinstance(object.position, self.AutoPlacement):
            return object

        def spawn_below_previous_object() -> PointSpecifier:
            previous_object = self.get_previous_auto_positioned_child(object)
            # Align the object to the middle of the container along the cross-axis (x-axis)
            container_midpoint_x = self.collision_box().center()[0]
            x_spawn_point = Pixels(container_midpoint_x, position=CENTER)
            print(f"Placing {object} below previous object: {previous_object}")
            y_spawn_point = (
                BelowObject(previous_object) if previous_object else self.spawn_at.y
            )
            return PointSpecifier(
                x_spawn_point, y_spawn_point, self_corner=Corner.TOP_LEFT
            )

        object.position = spawn_below_previous_object()
        return object

    def add_children(self, *objects: GameObject):
        for object in objects:
            if object in self._children:
                raise RuntimeError(f"{object} is already a child of {self}")
        self._children.extend(objects)
        self.game.all_objects.extend(objects)

    def remove_all_children(self):
        for child in self._children:
            self.game.all_objects.remove(child)
        self._children.clear()

    def list_children(self):
        return self._children.copy()

    def remove_child(self, child: GameObject):
        self._children.remove(child)
        self.game.all_objects.remove(child)

    def run_child_tick_tasks(self):
        for child in self._children:
            child.run_tick_tasks()

    def get_widest_child(self) -> GameObject | None:
        widest_child = None
        for child in self._children:
            if widest_child is None or child.width() > widest_child.width():
                widest_child = child
        return widest_child


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
        self.page_title_object = Text(
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


class Text(GameObject):
    def spawn_point(self) -> PointSpecifier:
        return self.spawn_at

    def __init__(
        self,
        game: Monopoly,
        get_content: Callable[[], str],
        spawn_at: PointSpecifier,
        font: Font | None = None,
        color: Color | None = None,
        padding: tuple[float, float] = (0, 0),
    ) -> None:
        self.spawn_at = spawn_at
        font = font or game.fonts.body()
        super().__init__(
            game=game,
            texture=TextTexture(game, get_content, font, color, padding),
        )


class ButtonTexture(TextTexture):
    def __init__(
        self,
        game: Monopoly,
        object: Button,
        get_content: Callable[[], str | Tuple[str, Color]],
        font: Font,
        base_color: Color,
    ):
        super().__init__(game, get_content, font)
        self.button = object
        self.base_color = base_color

    def get_background_color(self) -> Color | None:
        # Lighten the color if the button is hovered or pressed
        hover_color = self.base_color.lerp("white", 0.4)
        pressed_color = self.base_color.lerp("white", 0.6)
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
    ):
        # self.game = game
        self.label = label
        self.callback = callback
        self.spawn_at = spawn_at
        self.font = font or game.fonts.button()
        self.texture = ButtonTexture(
            game, self, self.get_content, self.font, Color("green")
        )
        super().__init__(game, self.texture)
        self.on_click_tasks.append(self.run_callback)

    def run_callback(self, _):
        self.callback()

    def get_content(self):
        return self.label

    def spawn_point(self) -> PointSpecifier:
        return self.spawn_at
