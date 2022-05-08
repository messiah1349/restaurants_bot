import re

import pandas as pd
from typing import Callable, Optional, Union

import telebot

from lib.scenario.base import Scenario
from lib.scenario.utils import (
    create_keyboard,
    create_inline_keyboard,
    save_table_as_image
)
from lib.scenario.mark import create_change_mark_menu

TAX = 1.1


class CreatePayment(Scenario):
    def __init__(self, parent: "Scenario", is_smart: bool, bot: "telebot.TeleBot", backend: "Backend"):
        self.is_smart = is_smart
        super().__init__(parent, bot, backend)

    def get_name(self) -> str:
        return "Создать платеж" if not self.is_smart else "Создать SmartShare™ платеж"

    def start(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id

        response = self.backend.get_users_list()

        if response.status != 1:
            self.bot.send_message(send_id, "Что-то пошло нет так.")
            return

        if len(response.answer) < 2:
            self.bot.send_message(send_id, "Зарегистрирован лишь один пользователь")
            return

        user_name_to_id = {user["name"]: user["telegram_id"] for user in response.answer}
        sender_name = None

        for name, user_id in user_name_to_id.items():
            if user_id == send_id:
                sender_name = name

        assert sender_name is not None
        print(sender_name)

        call_params = {
            "creator_id": send_id,
            "payment_type": "other",
            "payment_datetime": None,
            "is_resolved": False,
            "restaurant_id": None,
            "shares": {}
        }

        self.state = {
            "params": dict(call_params),
            "tip_params": dict(call_params),
            "users": user_name_to_id,
            "sender_name": sender_name
        }

        keyboard = create_keyboard(list(user_name_to_id.keys()))

        if self.is_smart:
            self.bot.send_message(send_id, """
Приготовься создавать платеж по технологии SmartShare!™
- Не считай 10% налог
- Отдельно вводи чаевые
- Используй бота, как калькулятор
            """)
            self.state["smart_share"] = [{"name": name, "payment": None} for name in user_name_to_id.keys()]
            # move payer to the beginning
            self.state["smart_share"].sort(key=lambda x: -1 if x["name"] == sender_name else 1)
            self.state["smart_tips"] = [{"name": name, "payment": None} for name in user_name_to_id.keys()]

            self.state["smart_share_index"] = 0

        self.bot.send_message(send_id, "Кто заплатил?", reply_markup=keyboard)

        return self.handle_payer

    def handle_payer(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id
        payer_name = message.text

        if payer_name not in self.state["users"]:
            self.bot.send_message(send_id, "Просто выбери из списка, долбоеб. Ничего не пиши.")
            return

        payer_id = self.state["users"][payer_name]
        self.state["params"]["payer"] = payer_id

        response = self.backend.get_restaurant_list()
        if response.status != 1:
            self.bot.send_message(send_id, "Не могу получить рестораны")
            return

        self.state["restaurants"] = {r["name"]: r["restaurant_id"] for r in response.answer}
        keyboard = create_keyboard(list(self.state["restaurants"].keys()))

        msg = f"За что заплатил {payer_name}?\nВыберите ресторан или введите комментарий платежа"
        self.bot.send_message(send_id, msg, reply_markup=keyboard)
        return self.handle_comment

    def handle_comment(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id

        if not message.text:
            self.bot.send_message(send_id, "Введи текст")
            return self.handle_comment
        elif message.text in self.state["restaurants"]:
            self.state["params"]["comment"] = message.text.replace("\n", " ")
            self.state["params"]["restaurant_id"] = int(self.state["restaurants"][message.text])
            self.state["params"]["payment_type"] = "restaurant"
            self.state["restaurant_name"] = message.text

            self.bot.send_message(send_id, f"Оплата ресторана {message.text}.\nСколько заплатил?")
            return self.handle_total
        else:
            self.state["params"]["comment"] = message.text.replace("\n", " ")
            self.state["params"]["payment_type"] = "other"

            keyboard_remove = telebot.types.ReplyKeyboardRemove()
            self.bot.send_message(send_id, f"Оплата '{message.text}'.\nСколько заплатил?", reply_markup=keyboard_remove)
            return self.handle_total

    def handle_total(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id
        try:
            total = float(message.text)
        except ValueError:
            self.bot.send_message(send_id, "Введи число")
            return self.handle_total

        if total <= 0:
            self.bot.send_message(send_id, "Сумма должна быть положительной")
            return self.handle_total

        self.state["params"]["total"] = total

        if self.is_smart and self.state["params"]["restaurant_id"] is not None:
            next_payer = self.ask_next_smart_payer()
            msg = f"""
Введи цену за каждое блюдо или просуммируй как лох самостоятельно.
Не учитывай никакие налоги, просто перепиши цифры из чека.
Например:
1300 + 2500 + 1200
1000+400+88
или
5000

{next_payer}:
            """

            self.bot.send_message(send_id, msg)
            return self.handle_smart_share_loop
        else:
            msg = "Сколько должен заплатить каждый?"

            keyboard = create_keyboard(["Поровну", "Не поровну", "Один на Х больше, чем другие"])
            self.bot.send_message(send_id, msg, reply_markup=keyboard)

            return self.handle_same_shares

    def ask_next_smart_payer(self) -> Optional[str]:
        if self.smart_payers_to_fill_count() == 0:
            return

        while True:
            index = self.state["smart_share_index"]
            name_and_payment = self.state["smart_share"][index]

            if name_and_payment["payment"] is None:
                name = name_and_payment["name"]
                break

            self.state["smart_share_index"] = (index + 1) % len(self.state["smart_share"])

        return name

    def fill_smart_payment(self, value: int) -> Optional[str]:
        index = self.state["smart_share_index"]
        self.state["smart_share"][index]["payment"] = value
        self.state["smart_share_index"] = (index + 1) % len(self.state["smart_share"])

    def smart_payers_to_fill_count(self) -> int:
        return len([x for x in self.state["smart_share"] if x["payment"] is None])

    def parse_smart_share_tip(self, text: str) -> Union[int, str]:
        try:
            value = int(text)
        except ValueError:
            return "Введи число"

        if value < 0:
            return "Неотрицательное число нужно"

        return value

    def parse_smart_share_payment(self, text: str) -> Union[int, str]:
        is_matched = re.match("^(\d|[\.\+\-\*\/]| )+$", text) is not None

        if not is_matched:
            return "Цифры, арифметические действия и пробелы только"

        try:
            value = eval(text)
        except SyntaxError:
            return "Такое не распарсить, скорее всего ты идиот"

        if value < 0:
            return "Нельзя отрицательное вводить. Тупой."

        current_total = sum(item["payment"] for item in self.state["smart_share"]
                            if item["payment"] is not None)

        if (current_total + value) * TAX > self.state["params"]["total"]:
            return "Слишком много вышло. Заново вводи"

        value *= TAX

        return value

    def fill_last_smart_payer(self) -> None:
        total = self.state["params"]["total"]

        rest = total - sum(item["payment"] for item in self.state["smart_share"]
                           if item["payment"] is not None)
        self.fill_smart_payment(rest)

    def handle_smart_share_loop(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id

        payers_to_fill = self.smart_payers_to_fill_count()
        assert payers_to_fill > 1

        value = self.parse_smart_share_payment(message.text)
        if isinstance(value, str):
            self.bot.send_message(send_id, value)
            return self.handle_smart_share_loop
        else:
            self.fill_smart_payment(value)
            if payers_to_fill - 1 > 1:
                next_payer = self.ask_next_smart_payer()
                self.bot.send_message(send_id, f"{next_payer}:")
                return self.handle_smart_share_loop
            else:
                self.fill_last_smart_payer()
                keyboard = create_keyboard(["Да", "Нет"])
                self.bot.send_message(send_id, f"Чаевые?", reply_markup=keyboard)
                return self.handle_tips

    def handle_tips(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id
        if message.text == "Да":
            keyboard = create_keyboard(list(self.state["users"].keys()))
            self.bot.send_message(send_id, f"Кто заплатил чаевые?", reply_markup=keyboard)
            return self.handle_tips_payer
        else:
            self.bot.send_message(send_id, f"Пидора ответ")
            self.finalize_smart_payment(send_id)
            return

    def handle_tips_payer(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id
        payer_name = message.text

        if payer_name not in self.state["users"]:
            self.bot.send_message(send_id, "Просто выбери из списка, долбоеб. Ничего не пиши.")
            return

        payer_id = self.state["users"][payer_name]
        self.state["tip_params"]["payer"] = payer_id
        self.state["tip_payer_name"] = payer_name

        self.bot.send_message(send_id, "Сколько заплатил?")
        return self.handle_tips_payment

    def handle_tips_payment(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id
        try:
            value = int(float(message.text))
        except ValueError:
            self.bot.send_message(send_id, "Введи число")
            return self.handle_tips_payment

        if value <= 0:
            self.bot.send_message(send_id, "Введи положительное число")
            return self.handle_tips_payment

        self.state["tip_params"]["total"] = value

        user_ids = list(self.state["users"].values())
        id_to_share = {user_id: round(value / len(user_ids)) for user_id in user_ids}

        self.state["tip_params"]["shares"] = id_to_share
        self.state["tip_params"]["comment"] = "(чай) " + self.state["params"]["comment"]

        self.finalize_smart_payment(send_id)

    def finalize_smart_payment(self, send_id):
        print("Finalizing")
        info_msg = []

        payer_name = list(filter(lambda user: user[1] == self.state["params"]["payer"],
                                 self.state["users"].items()))[0][0]

        info_msg.append(f"Уплатил: {payer_name}")
        info_msg.append(f"Чек: {self.state['params']['total']}")

        self.state["smart_share"] = {item["name"]: round(item["payment"]) for item in self.state["smart_share"]}

        smart_share_msg = "\n".join(f"{name}: {round(share / TAX)}"
                                    for name, share in self.state["smart_share"].items())
        info_msg.append(f"По чеку (без налога): \n{smart_share_msg}")

        smart_share_msg = "\n".join(f"{name}: {share}" for name, share in self.state["smart_share"].items())
        info_msg.append(f"По чеку (с налогом): \n{smart_share_msg}")

        has_tips = "total" in self.state["tip_params"]

        if has_tips:
            tip_total = self.state["tip_params"]["total"]
            min_tip = min(self.state["tip_params"]["shares"].values())
            max_tip = max(self.state["tip_params"]["shares"].values())
            assert min_tip == max_tip

            info_msg.append(f"Чаевые: {tip_total}\nУплатил: {self.state['tip_payer_name']}")
            info_msg.append(f"С каждого по {max_tip}")

        users = self.state["users"]
        id_to_share = {users[name]: share for name, share in self.state["smart_share"].items()}
        self.state["params"]["shares"] = id_to_share

        self.bot.send_message(send_id, "\n\n".join(info_msg))

        main_response = self.backend.add_payment(**self.state["params"])
        if main_response.status == 1:
            self.bot.send_message(send_id, "Основной платеж введен успешно!")
        else:
            self.bot.send_message(send_id, "Произошла ошибка, придется все заново делать!")
            return

        if has_tips:
            tips_response = self.backend.add_payment(**self.state["tip_params"])
            if tips_response.status == 1:
                self.bot.send_message(send_id, "Чаевые введены успешно!")
            else:
                self.bot.send_message(send_id, "Чаевые проебались, введи их отдельно!")
                return

        self.notify_mark_update()
        return

    def handle_same_shares(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id
        user_ids = list(self.state["users"].values())

        if message.text == "Поровну":
            total = self.state["params"]["total"]
            id_to_share = {user_id: total / len(user_ids) for user_id in user_ids}
            self.state["params"]["shares"] = id_to_share

            response = self.backend.add_payment(**self.state["params"])
            if response.status == 1:
                self.bot.send_message(send_id, "Успешно!")
                self.notify_mark_update()
            else:
                self.bot.send_message(send_id, "Произошла ошибка, придется все заново делать!")
            return
        elif message.text == "Не поровну":
            names = list(self.state["users"].keys())
            shares_info = {"names": names, "index": 0, "rest": self.state["params"]["total"]}

            cur_name = shares_info["names"][shares_info['index']]

            self.state["shares_info"] = shares_info

            self.bot.send_message(send_id, f"{cur_name} должен уплатить:\n")

            return self.handle_share_loop
        elif message.text == "Один на Х больше, чем другие":
            names = list(self.state["users"].keys())

            keyboard = create_keyboard(names)
            self.bot.send_message(send_id, "Кто должен заплатить больше?", reply_markup=keyboard)

            return self.handle_who_pays_more
        else:
            self.bot.send_message(send_id, "Неправильный ввод")
            return self.handle_same_shares

    def notify_mark_update(self):
        if self.state["params"]["restaurant_id"] is None:
            return
        for user_id in self.state["users"].values():
            create_change_mark_menu(
                bot=self.bot,
                send_id=user_id,
                restaurant_name=self.state["restaurant_name"],
                restaurant_id=self.state["params"]["restaurant_id"]
            )

    def handle_who_pays_more(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id
        names = list(self.state["users"].keys())
        if message.text not in names:
            self.bot.send_message(send_id, "Выбери из списка")
            return self.handle_who_pays_more
        else:
            self.state["who_pays_more"] = message.text
            self.bot.send_message(send_id, f"На сколько больше {message.text} должен заплатить?")
            return self.handle_pay_difference

    def handle_pay_difference(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id
        total = self.state["params"]["total"]
        user_ids = list(self.state["users"].values())
        try:
            diff = float(message.text)
        except ValueError:
            self.bot.send_message(send_id, "Введи число")
            return self.handle_pay_difference

        if diff >= total:
            msg = f"Нельзя заплатить на {diff} больше, если общий чек {total}"
            self.bot.send_message(send_id, msg)
            return self.handle_pay_difference

        common_part = (total - diff) / len(user_ids)
        id_to_share = {user_id: common_part for user_id in user_ids}

        who_pays_more_name = self.state["who_pays_more"]
        who_pays_more_id = self.state["users"][who_pays_more_name]

        largest_share = common_part + diff

        id_to_share[who_pays_more_id] = largest_share
        self.state["params"]["shares"] = id_to_share

        response = self.backend.add_payment(**self.state["params"])
        if response.status == 1:
            msg = f"Успешно! {who_pays_more_name} платит {largest_share}, остальные - {common_part}"
            self.bot.send_message(send_id, msg)
            self.notify_mark_update()
        else:
            self.bot.send_message(send_id, "Произошла ошибка, придется все заново делать!")
        return

    def _get_cur_name(self) -> Optional[str]:
        si = self.state["shares_info"]
        return si["names"][si["index"]] if si["index"] < len(si["names"]) else None

    def _proceed_share_input(self) -> Optional[str]:
        si = self.state["shares_info"]
        si["index"] += 1
        return self._get_cur_name()

    def _last_share_left(self) -> bool:
        si = self.state["shares_info"]
        return si["index"] == len(si["names"]) - 1

    def handle_share_loop(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.chat.id
        try:
            number = float(message.text)

            if number > self.state["shares_info"]["rest"]:
                self.bot.send_message(send_id, f"Слишком много ({self.state['shares_info']['rest']} осталось)")
                return self.handle_share_loop
        except ValueError:
            self.bot.send_message(send_id, "Введи число")
            return self.handle_share_loop

        if number <= 0:
            self.bot.send_message(send_id, "Введи положительное число")
            return self.handle_share_loop

        name = self._get_cur_name()
        user_id = self.state["users"][name]

        self.state["params"]["shares"][user_id] = number
        self.state["shares_info"]["rest"] -= number

        self._proceed_share_input()
        name = self._get_cur_name()

        if self._last_share_left():
            user_id = self.state["users"][name]
            rest_share = self.state["shares_info"]["rest"]
            self.state["params"]["shares"][user_id] = rest_share

            self.bot.send_message(send_id, f"Стало быть, {name} платит {rest_share}")

            response = self.backend.add_payment(**self.state["params"])
            if response.status == 1:
                self.bot.send_message(send_id, "Успешно!")
                self.notify_mark_update()
            else:
                self.bot.send_message(send_id, "Что-то пошло не так, придется еще раз!!")
            return
        else:
            self.bot.send_message(
                send_id,
                f"Принято! Осталось раскидать {self.state['shares_info']['rest']}\n"
                f"{name} должен уплатить:"
            )
            return self.handle_share_loop


class ListPayments(Scenario):
    def get_name(self) -> str:
        return "Показать платежи"

    def start(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id
        response = self.backend.get_users_list()
        if response.status != 1:
            self.bot.send_message(send_id, "Что-то пошло не так, придется еще раз!!")
            return

        replace = {user["telegram_id"]: user["name"] for user in response.answer}

        payments = self.backend.get_unresolved_payment_list().answer

        if not len(payments):
            self.bot.send_message(send_id, "Таблица платежей пуста!")
            return

        payments = pd.DataFrame(payments)
        payments["payment"] = payments["comment"].str[:20] + " (" + payments["datetime_str"].str.split(" ").str[0] + ")"
        payments = payments[["payment", "payer", "total_sum"]]
        payments["payer"] = payments["payer"].replace(replace)

        payments = payments.rename({
            "payment": "Платеж",
            "total_sum": "Сумма",
            "payer": "Плательщик",
        }, axis=1).set_index("Платеж")

        img_name = f"tables/{send_id}_payments.png"
        save_table_as_image(payments, plot_index=True, output_file=img_name)

        with open(img_name, "rb") as ifile:
            self.bot.send_photo(send_id, ifile)


class RemovePayment(Scenario):
    def get_name(self) -> str:
        return "Удалить платеж"

    def start(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id
        response = self.backend.get_unresolved_payment_list()

        if response.status != 1:
            self.bot.send_message(send_id, "Что-то пошло не так, придется еще раз!!")
            return

        payments = response.answer

        if not len(payments):
            self.bot.send_message(send_id, "Нечего удалять!")
            return

        response = self.backend.get_users_list()

        if response.status != 1:
            self.bot.send_message(send_id, "Что-то пошло не так, придется еще раз!!")
            return

        users = response.answer
        id_to_name = {user["telegram_id"]: user["name"] for user in users}

        self.text_to_id = {
            f"{id_to_name[p['payer']]} ({p['total_sum']}, {p['datetime_str']})": p["payment_id"]
            for p in payments
        }

        keyboard = create_keyboard(list(self.text_to_id.keys()))
        self.bot.send_message(send_id, "Выберите платеж:", reply_markup=keyboard)
        return self.handle_payment

    def handle_payment(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id

        if message.text not in self.text_to_id:
            self.bot.send_message(send_id, "Такого платежа нет, попробуйте еще раз")
            return self.handle_payment

        payment_id = self.text_to_id[message.text]

        response = self.backend.delete_payment(payment_id)
        if response.status == 1:
            self.bot.send_message(send_id, "Платеж успешно удален!")
        else:
            self.bot.send_message(send_id, "Что-то пошло не так, придется еще раз!")


class ListOwes(Scenario):
    def get_name(self) -> str:
        return "Показать долги"

    def start(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id
        response = self.backend.get_owes()
        if response.status != 1:
            self.bot.send_message(send_id, "Что-то пошло не так, придется еще раз!")
            return

        owes = pd.DataFrame(response.answer)

        if owes.empty:
            self.bot.send_message(send_id, "Таблица долгов пуста!")
            return

        owes = owes[["user_from", "user_to", "owe"]]

        owes = owes.query("owe>1").sort_values("owe", ascending=False).copy()

        owes.rename({
            "user_from": "Кто",
            "user_to": "Кому",
            "owe": "Сколько",
        }, axis=1, inplace=True)

        img_name = f"tables/{send_id}_owes.png"
        save_table_as_image(owes, plot_index=False, output_file=img_name)

        with open(img_name, "rb") as ifile:
            self.bot.send_photo(send_id, ifile)


class ResolvePayments(Scenario):
    def get_name(self) -> str:
        return "Обнулиться"

    def start(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id
        response = self.backend.resolve(creator_id=send_id)

        if response.status == 1:
            self.bot.send_message(send_id, "Все долги обнулены!")
        else:
            self.bot.send_message(send_id, "Что-то пошло не так, придется еще раз!")


class OweReminder(Scenario):
    def get_name(self) -> str:
        return "Напомнить о долге"

    def start(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id
        response = self.backend.get_owes()

        if response.status != 1:
            self.bot.send_message(send_id, "Что-то пошло не так, придется еще раз!")
            return

        owes = pd.DataFrame(response.answer)
        if owes.empty:
            self.bot.send_message(send_id, "Никто никому не должен")
            return

        owes = owes.query("id_to==@send_id")

        if owes.empty:
            self.bot.send_message(send_id, "Вам никто ничего не должен")
        else:
            msg = "\n".join([
                "Вам должны денег:",
                "\n".join(owes["user_from"]),
                "\n",
                "Уведомим."
            ])
            self.bot.send_message(send_id, msg)
            name = owes.iloc[0]["user_to"]

            for debtor_id in owes["id_from"]:
                self.bot.send_message(debtor_id, f"Ты должен денег {name}, пидрила")
