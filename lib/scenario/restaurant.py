import pandas as pd
from typing import Optional, Callable, Union

import telebot.types

from lib.scenario.base import Scenario
from lib.scenario.utils import (
    create_inline_keyboard,
    create_keyboard,
    save_table_as_image
)


class RestaurantInviter(Scenario):
    def get_name(self) -> str:
        return "Пригласить в ресторан"

    def start(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id

        response = self.backend.get_users_list()

        if response.status != 1:
            self.bot.send_message(send_id, "Ошибка. Попробуйте еще.")
            return

        users_to_invite = []

        for user in response.answer:
            if user["telegram_id"] == send_id:
                user_name = user["name"]
                user_id = user["telegram_id"]
            else:
                users_to_invite.append(user["telegram_id"])

        for user_to_invite in users_to_invite:
            self.bot.send_message(user_to_invite, f"{user_name} предлагает вам сходить в ресторан")

        self.bot.send_message(user_id, "Все пользователи были уведомлены!")


class CreateRestaurant(Scenario):
    FLAG_ATTR_TEXTS = {
        "is_fast": ["Залупски долго ждать", "Быстро похавать"],
        "is_near": ["В ебенях", "Недалеко"],
        "is_new": ["Уже были тут ранее", "Место неизведанное"]
    }

    def get_name(self) -> str:
        return "Создать ресторан"

    def start(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id

        self.bot.send_message(send_id, "Как называется ресторан?")
        self.state = {
            "params": {
                "is_fast": False,
                "is_near": False,
                "is_new": True
            },
            "attr_msg": None
        }

        return self.handle_name

    def handle_name(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id
        self.state["params"]["restaurant_name"] = message.text

        attr_keyboard = create_inline_keyboard(
            button_texts=["Быстро?", "Близко?", "Были тут?"],
            callback_values=["is_fast", "is_near", "is_new"]
        )
        attr_msg = self._construct_attr_msg()
        send_msg_data = self.bot.send_message(send_id, attr_msg, reply_markup=attr_keyboard)
        self.state["attr_msg"] = send_msg_data.message_id
        self.state["inline_keyboard"] = attr_keyboard
        self.accept_callback = True

        finish_keyboard = create_keyboard(["Готово", "Отмена"])
        finish_msg = "Когда закончишь, нажмешь Готово."
        self.bot.send_message(send_id, finish_msg, reply_markup=finish_keyboard)

        return self.handle_attributes

    def _handle_callback(self, message: "telebot.types.CallbackQuery") -> None:
        send_id = message.from_user.id
        callback = message.data

        if callback in CreateRestaurant.FLAG_ATTR_TEXTS:
            self.state["params"][callback] = not self.state["params"][callback]
            msg = self._construct_attr_msg()

            self.bot.edit_message_text(
                chat_id=send_id,
                message_id=self.state["attr_msg"],
                text=msg,
                reply_markup=self.state["inline_keyboard"]
            )

    def _handle_message(self, message: "telebot.types.Message") -> None:
        send_id = message.from_user.id
        text = message.text

        if text == "Готово":
            send_id = message.from_user.id

            response = self.backend.add_restaurant(**self.state["params"])

            if response.status == 1:
                self.bot.send_message(send_id, "Ресторан успешно добавлен")
                self.accept_callback = False
            else:
                msg = f"Произошла хуйня следующего содержания:\n{response.answer}"
                self.bot.send_message(send_id, msg)
        elif text == "Отмена":
            self.bot.send_message(send_id, "Галя, у нас отмена!!")
        else:
            self.bot.send_message(send_id, "Опять ввел хуйню.")

    def handle_attributes(self, message: Union["telebot.types.Message", "telebot.types.CallbackQuery"]) -> Optional[Callable]:
        if isinstance(message, telebot.types.CallbackQuery):
            self._handle_callback(message)
            return self.handle_attributes
        elif isinstance(message, telebot.types.Message):
            self._handle_message(message)
            return
        else:
            return

    def _construct_attr_msg(self):
        msg = [f"Ресторан: {self.state['params']['restaurant_name']}"]
        for flag_name, text_pair in CreateRestaurant.FLAG_ATTR_TEXTS.items():
            text_index = int(self.state["params"][flag_name])
            msg.append(text_pair[text_index])

        return "\n".join(msg)

class ListRestaurants(Scenario):
    def get_name(self) -> str:
        return "Показать рестораны"

    def start(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id

        response = self.backend.get_restaurant_list()
        if response.status != 1:
            self.bot.send_message(send_id, f"Что-то пошло не так:\n{response.answer}")
            return

        restaurants = pd.DataFrame(response.answer)

        if restaurants.empty:
            self.bot.send_message(send_id, "Таблица ресторанов пуста!")
            return

        restaurants = restaurants[["name", "is_fast", "is_near", "is_new"]]

        restaurants.rename({
            "name": "Название",
            "is_fast": "Быстро",
            "is_near": "Рядом",
            "is_new": "Новый",
        }, axis=1, inplace=True)

        restaurants = restaurants\
                .set_index("Название")\
                .astype(bool)\
                .replace({True: "Да", False: "Нет"})

        img_name = f"tables/{send_id}_restaurants.png"
        save_table_as_image(restaurants, plot_index=True, output_file=img_name)

        with open(img_name, "rb") as ifile:
            self.bot.send_photo(send_id, ifile)


class RemoveRestaurant(Scenario):
    def get_name(self) -> str:
        return "Удалить ресторан"

    def start(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id

        response = self.backend.get_restaurant_list()
        if response.status != 1:
            self.bot.send_message(send_id, f"Что-то пошло не так:\n{response.answer}")
            return

        restaurants = response.answer

        if not len(restaurants):
            self.bot.send_message(send_id, "Нечего удалять!")
            return

        self.state["name_to_id"] = {r["name"]: r["restaurant_id"] for r in restaurants}
        buttons = list(self.state["name_to_id"].keys()) + ["Отмена"]

        keyboard = create_keyboard(buttons)
        self.bot.send_message(send_id, "Выберите ресторан:", reply_markup=keyboard)
        return self.handle_restaurant

    def handle_restaurant(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id

        if message.text == "Отмена":
            self.bot.send_message(send_id, "Галя, у нас отмена!!")
            return

        if message.text not in self.state["name_to_id"]:
            self.bot.send_message(send_id, "Такого ресторана нет, попробуйте еще раз")
            return self.handle_restaurant

        restaurant_id = self.state["name_to_id"][message.text]

        response = self.backend.remove_restaurant(restaurant_id)

        if response.status == 1:
            self.bot.send_message(send_id, "Ресторан успешно удален!")
        else:
            self.bot.send_message(send_id, "Что-то пошло не так, придется еще раз!")


class SelectRandomRestaurant(Scenario):
    FILTER_INFO = {
        "is_near": [("Поближе", True), ("Похуй", None)],
        "is_fast": [("Побыстрее", True), ("Похуй", None)],
        "is_new": [("Новый", True), ("Старый", False), ("Похуй", None)],
    }

    FILTER_NAMES = {
        "is_near": "Рядом?",
        "is_fast": "Быстро готовят?",
        "is_new": "Новый или старый?"
    }


    def get_name(self) -> str:
        return "Выбрать случайный ресторан"

    def start(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id

        self.state = {
            "filters": {
                "is_fast": None,
                "is_near": None,
                "is_new": None
            }
        }

        filter_keyboard = create_inline_keyboard(
            button_texts=["Не хочу далеко идти", "Не хочу долго ждать", "Хочу в новое место"],
            callback_values=["is_near", "is_fast", "is_new"]
        )

        filter_msg = self._construct_filter_msg()
        send_msg_data = self.bot.send_message(send_id, filter_msg, reply_markup=filter_keyboard)
        self.state["msg_id"] = send_msg_data.message_id
        self.state["inline_keyboard"] = filter_keyboard
        self.accept_callback = True

        finish_keyboard = create_keyboard(["Готово", "Отмена"])
        finish_msg = "Выбери фильтры и нажми Готово."
        self.bot.send_message(send_id, finish_msg, reply_markup=finish_keyboard)

        return self.handle_filters

    def _construct_filter_msg(self):
        msg = ["Текущие фильтры:\n"]
        for filt, items in SelectRandomRestaurant.FILTER_INFO.items():
            for text, value in items:
                if self.state["filters"][filt] == value:
                    prefix = SelectRandomRestaurant.FILTER_NAMES[filt]
                    msg.append(f"{prefix} {text}")

        return "\n".join(msg)

    def _switch_filter(self, filter_name):
        switch_cases = SelectRandomRestaurant.FILTER_INFO[filter_name]
        current_value = self.state["filters"][filter_name]
        for index, (text, value) in enumerate(switch_cases):
            if current_value == value:
                next_index = (index + 1) % len(switch_cases)
                next_value = switch_cases[next_index][1]
                self.state["filters"][filter_name] = next_value
                return

        raise ValueError("Can't set next value")

    def _handle_callback(self, message: "telebot.types.CallbackQuery") -> None:
        send_id = message.from_user.id
        callback = message.data

        if callback in SelectRandomRestaurant.FILTER_INFO:
            self._switch_filter(callback)
            msg = self._construct_filter_msg()

            self.bot.edit_message_text(
                chat_id=send_id,
                message_id=self.state["msg_id"],
                text=msg,
                reply_markup=self.state["inline_keyboard"]
            )

    def _handle_message(self, message: "telebot.types.Message") -> None:
        send_id = message.from_user.id
        text = message.text

        if text == "Готово":
            send_id = message.from_user.id
            print(self.state["filters"])

            self.backend.get_random_restaurant(**self.state["filters"])

            if response.status != 1:
                msg = f"Произошла хуйня следующего содержания:\n{response.answer}"
                self.bot.send_message(send_id, msg)
                return
            restaurants = response.answer

            # restaurants = [
            #     {"restaurant_name": "zalupa", "restaurant_id": 1},
            #     {"restaurant_name": "piska", "restaurant_id": 2},
            #     {"restaurant_name": "chlennica", "restaurant_id": 3}
            # ]

            if not len(restaurants):
                self.bot.send_message(send_id, "Список пуст, необходимо опохуить фильтры")
                return

            self.accept_callback = False

            msg = f"Представляем вашему вниманию ресторан: {restaurants[0]['restaurant_name']}"
            keyboard = create_keyboard(["Ок!", "Дальше"])

            self.bot.send_message(send_id, msg, reply_markup=keyboard)
            self.state["ranked_restaurants"] = restaurants
            self.state["cur_rank"] = 0
            return self.handle_next_restaurant
        elif text == "Отмена":
            self.bot.send_message(send_id, "Галя, у нас отмена!!")
        else:
            self.bot.send_message(send_id, "Опять ввел хуйню.")

    def handle_filters(self, message: Union["telebot.types.Message", "telebot.types.CallbackQuery"]) -> Optional[Callable]:
        if isinstance(message, telebot.types.CallbackQuery):
            self._handle_callback(message)
            return self.handle_filters
        elif isinstance(message, telebot.types.Message):
            return self._handle_message(message)
        else:
            return

    def handle_next_restaurant(self, message: "telebot.types.Message") -> None:
        send_id = message.from_user.id
        restaurants = self.state["ranked_restaurants"]

        if message.text == "Ок!":
            chosen = restaurants[self.state["cur_rank"]]["restaurant_name"]
            self.bot.send_message(send_id, f"Поздравляю! Вы идете в {chosen}")
            return

        self.state["cur_rank"] += 1

        if self.state["cur_rank"] < len(restaurants):
            cur_restaurant = restaurants[self.state["cur_rank"]]["restaurant_name"]

            keyboard = create_keyboard(["Ок!", "Дальше"])
            msg = f"Тогда может быть ресторан {cur_restaurant}?"

            self.bot.send_message(send_id, msg, reply_markup=keyboard)

            return self.handle_next_restaurant
        else:
            self.bot.send_message(send_id, "Хуяльше! Рестораны кончились, до свидания.")
            return
