from typing import Optional, Callable

from lib.scenario.base import Scenario


class RegisterUser(Scenario):
    def get_name(self) -> str:
        return "Зарегистрироваться"

    def start(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id
        self.bot.send_message(send_id, "Введите имя")
        return self.finish_registration

    def finish_registration(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id

        user_name = message.text

        response = self.backend.add_user(telegram_id=send_id, user_name=user_name)

        if response.status == 1:
            self.bot.send_message(send_id, f"Поздравляем, {user_name}! Вы добавлены в сеть Ереван Ресторан")
        else:
            self.bot.send_message(send_id, "Какая-то проблема, идите нахуй")


class ListUsers(Scenario):
    def get_name(self) -> str:
        return "Список пользователей"

    def start(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id

        response = self.backend.get_users_list()
        if response.status != 1:
            self.bot.send_message(send_id, "Какая-то проблема, идите нахуй")
            return

        user_names = [user["name"] for user in response.answer]
        if not len(user_names):
            msg = "Список пользователей сети Ереван Ресторан пуст"
        else:
            msg = "Список пользователей сети Ереван Ресторан:\n" + "\n".join(user_names)

        self.bot.send_message(send_id, msg)


class ChangeUserName(Scenario):
    def get_name(self) -> str:
        return "Поменять имя"

    def start(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id
        self.bot.send_message(send_id, "Какое имя вы желаете?")
        return self.change_name

    def change_name(self, message: "telebot.types.Message") -> Optional[Callable]:
        send_id = message.from_user.id

        new_name = message.text
        response = self.backend.change_user_name(message.from_user.id, new_name)

        if response.status == 1:
            self.bot.send_message(send_id, f"Теперь ваше имя {new_name}")
        else:
            self.bot.send_message(send_id, "Какая-то проблема, идите нахуй")
