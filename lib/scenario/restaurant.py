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
                your_name = user["name"]
            else:
                users_to_invite.append(user["telegram_id"])

        for other_id in other_ids:
            self.bot.send_message(other_id, f"{your_name} предлагает вам сходить в ресторан")
