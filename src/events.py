from enum import Enum


class GameEvent(Enum):
    CLICK = "click"
    OBJECT_REMOVE = "object_remove"
    BEFORE_SPAWN = "before_first_draw"


class EventEmitter:
    def __init__(self):
        self.listeners = {event_type.value: {} for event_type in GameEvent}

    def on(self, event_name: GameEvent, callback):
        event_id = object()
        if event_name.value not in self.listeners:
            self.listeners[event_name.value] = {}
        self.listeners[event_name.value][event_id] = callback
        return event_id

    def emit(self, event_name: GameEvent, *args, **kwargs):
        if event_name.value in self.listeners:
            callbacks = list(self.listeners[event_name.value].values())
            for callback in callbacks:
                callback(*args, **kwargs)

    def remove_listener(self, event_name: GameEvent, event_id):
        if (
            event_name.value in self.listeners
            and event_id in self.listeners[event_name.value]
        ):
            del self.listeners[event_name.value][event_id]
