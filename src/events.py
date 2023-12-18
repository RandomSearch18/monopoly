from enum import Enum


class Event(Enum):
    CLICK = "click"
    OBJECT_REMOVE = "object_remove"


class EventEmitter:
    def __init__(self):
        self.listeners = {event_type.value: {} for event_type in Event}

    def on(self, event_name: Event, callback):
        event_id = object()
        if event_name.value not in self.listeners:
            self.listeners[event_name.value] = {}
        self.listeners[event_name.value][event_id] = callback
        return event_id

    def emit(self, event_name: Event, *args, **kwargs):
        if event_name.value in self.listeners:
            callbacks = list(self.listeners[event_name.value].values())
            for callback in callbacks:
                callback(*args, **kwargs)

    def remove_listener(self, event_name: Event, event_id):
        if (
            event_name.value in self.listeners
            and event_id in self.listeners[event_name.value]
        ):
            del self.listeners[event_name.value][event_id]
