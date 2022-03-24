from typing import Optional, Callable

from lib.scenario.base import Scenario


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
