import pandas as pd
from typing import Optional, Callable

from lib.scenario.base import Scenario
from lib.scenario.utils import (
    create_inline_keyboard,
    create_keyboard,
    save_table_as_image
)

MARKS_TEXTS = [
    "Очень хочу",
    "Хочу",
    "Средне",
    "Не хотелось бы",
    "Ужасно"
]


def create_change_mark_menu(bot, send_id, restaurant_name, restaurant_id):
    msg = f"Введите оценку ресторану {restaurant_name}"
    callback_values = [f"{text}*{restaurant_id}" for text in MARKS_TEXTS]
    keyboard = create_inline_keyboard(MARKS_TEXTS, callback_values, "RestaurantMarkChanged")
    bot.send_message(send_id, msg, reply_markup=keyboard)


class ChangeRestaurantMarkScenario(Scenario):
    def get_name(self) -> str:
        return "Обновить оценку ресторану"

    def start(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id
        response = self.backend.get_restaurant_list()
        if response.status != 1:
            self.bot.send_message(send_id, "Не могу получить рестораны")
            return

        self.state["name_to_id"] = {r["name"]: r["restaurant_id"] for r in response.answer}

        keyboard = create_keyboard(list(self.state["name_to_id"].keys()))

        self.bot.send_message(send_id, "Выберите ресторан", reply_markup=keyboard)
        return self.handle_restaurant

    def handle_restaurant(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id

        if message.text not in self.state["name_to_id"]:
            self.bot.send_message(send_id, "Выбери из списка, долбоеб")
            return self.handle_restaurant

        restaurant_id = self.state["name_to_id"][message.text]
        create_change_mark_menu(self.bot, send_id, message.text, restaurant_id)

        keyboard = create_keyboard(["Завершить"])
        self.bot.send_message(send_id, "Нажмите Завершить", reply_markup=keyboard)

        return self.handle_finish

    def handle_finish(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id
        if message.text == "Завершить":
            self.bot.send_message(send_id, "Завершено")
        else:
            self.bot.send_message(send_id, "Так тоже пойдет")
        return


class ListRestaurantMarks(Scenario):
    def get_name(self) -> str:
        return "Показать оценки"

    def start(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id

        response = self.backend.get_restaurant_mark_list()

        if response.status != 1:
            self.bot.send_message(send_id, "Что-то пошло не так, идите нахуй")
            return

        marks = pd.DataFrame(response.answer)

        if marks.empty:
            self.bot.send_message(send_id, "Оценок нет!")
            return

        marks = pd.pivot_table(
            marks,
            index="restaurant_name",
            columns="user_name",
            values="mark",
            aggfunc=lambda x: ' '.join(x)
        ).fillna("-")

        img_name = f"tables/{send_id}_marks.png"
        save_table_as_image(marks, plot_index=True, output_file=img_name)

        with open(img_name, "rb") as ifile:
            self.bot.send_photo(send_id, ifile)


class ChangeRestaurantMarkEvent(Scenario):
    def get_name(self) -> str:
        return "Обновить оценку ресторану"

    def start(self, event: "event.Event") -> Optional[Callable]:
        mark, restaurant_id = event.callback_value.split("*")
        restaurant_id = int(restaurant_id)
        response = self.backend.add_restaurant_mark(restaurant_id, event.sender_id, mark)

        if response.status == 1:
            message = event.data.message
            self.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=message.message_id,
                text=message.text + "\nОбновлено!",
                reply_markup=None
            )
        return
