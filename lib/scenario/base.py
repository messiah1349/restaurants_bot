from typing import Optional, Callable

from lib.scenario.utils import create_keyboard


class Scenario:
    """ Base scenario class.

    Derived classes should override get_name function and
    implement series of handlers, each of which returns next handler or None,
    if this handler is last.
    """

    def __init__(self, parent: "Scenario", bot: "telebot.TeleBot", backend: "Backend"):
        self.parent = parent
        self.bot = bot
        self.backend = backend

        self.children = []

        if parent is not None:
            parent.children.append(self)

        self.state = {}


class ScenarioList(Scenario):
    def __init__(self, parent: "Scenario", name: str, bot: "telebot.TeleBot", backend: "Backend"):
        self.name = name
        super().__init__(parent, bot, backend)

    def get_name(self) -> str:
        return self.name

    def start(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id

        names = [child.get_name() for child in self.children]
        self.name_to_index = {v: i for i, v in enumerate(names)}

        keyboard = create_keyboard(names)

        self.bot.send_message(send_id, "Выберите действие", reply_markup=keyboard)

        return self.select_child

    def select_child(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id

        if message.text not in self.name_to_index:
            self.bot.send_message(send_id, "Просто выбери из списка, долбоеб. Ничего не пиши")
            return

        index = self.name_to_index[message.text]

        return self.children[index].start(message)
