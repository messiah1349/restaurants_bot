import os

import telebot

from lib.backend import Backend
from lib.scenario import init_scenarios, init_events
from lib.scenario.event import try_parse_event


class ScenarioProcessor:
    def __init__(self, bot: "telebot.Telebot", backend: "Backend"):
        self.bot = bot
        self.backend = backend

        self.root_scenario = {}
        self.next_step = {}

    def handle_next(self, message=None):
        sid = message.from_user.id

        if sid not in self.next_step:
            self.root_scenario[sid] = init_scenarios(self.bot, self.backend)
            self.next_step[sid] = self.root_scenario[sid].start

        if isinstance(message, telebot.types.CallbackQuery):
            if not self._check_method_accepts_callbacks(self.next_step[sid]):
                self._send_callback_query_error(sid)
                return

        self.next_step[sid] = self.next_step[sid](message)

        if self.next_step[sid] is None:
            self.next_step[sid] = self.root_scenario[sid].start(message)

    def _check_method_accepts_callbacks(self, method):
        return method.__self__.accept_callback

    def _send_callback_query_error(self, sid):
        self.bot.send_message(sid, "Перестань сюда нажимать, долбоеб")


class EventProcessor:
    def __init__(self, bot: "telebot.Telebot", backend: "Backend"):
        self.bot = bot
        self.backend = backend

        self.subscribers = {}

    def register(self, event_type: str, subscriber: "Subscriber"):
        self.subscribers[event_type].append(subscriber)

    def process_event(self, event: "Event"):
        if event.sender_id not in self.subscribers:
            self.subscribers[event.sender_id] = init_events(self.bot, self.backend)

        for subscriber in self.subscribers[event.sender_id][event.event_type]:
            subscriber.start(event)


class Client:
    ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))

    BACKEND_SOURCES = {
        "prod": "prod.db",
        "testing": "testing.db"
    }

    def __init__(self, backend_source: str, token: str):
        assert backend_source in Client.BACKEND_SOURCES, "wrong backend source"

        db_name = Client.BACKEND_SOURCES[backend_source]
        db_path = (os.path.join(Client.ROOT_DIR, "data", db_name))

        self.backend = Backend(db_path)
        self.bot = telebot.TeleBot(token)

        self.scenario_processor = ScenarioProcessor(self.bot, self.backend)
        self.event_processor = EventProcessor(self.bot, self.backend)

        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_handler(call):
            event = try_parse_event(call)
            if event is not None:
                self.event_processor.process_event(event)
            else:
                self.scenario_processor.handle_next(call)

        @self.bot.message_handler(content_types=["text"])
        def message_handler(message):
            self.scenario_processor.handle_next(message)

    def run(self):
        self.bot.infinity_polling(timeout=10, long_polling_timeout=5)
