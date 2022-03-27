from typing import Any, Optional
from dataclasses import dataclass

SENTINEL = "|"


@dataclass
class Event:
    event_type: str
    sender_id: int
    data: Any
    callback_value: str


def try_parse_event(call: "telebot.types.CallbackQuery") -> Optional[Event]:
    if SENTINEL not in call.data:
        return
    event_type, value = call.data.split(SENTINEL, 1)
    return Event(event_type=event_type, sender_id=call.from_user.id, data=call, callback_value=value)


def sign_callback(value, event_type):
    assert SENTINEL not in event_type and SENTINEL not in event_type
    return f"{event_type}{SENTINEL}{value}"
