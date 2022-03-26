from lib.scenario.base import (
    ScenarioList
)

from lib.scenario.payment import (
    CreatePayment,
    ListPayments,
    RemovePayment,
    ListOwes,
    ResolvePayments,
    OweReminder
)

from lib.scenario.user import (
    RegisterUser,
    ListUsers,
    ChangeUserName,
)

from lib.scenario.restaurant import (
    RestaurantInviter,
    CreateRestaurant,
    ListRestaurants,
    RemoveRestaurant,
    SelectRandomRestaurant
)


def init_scenarios(bot, backend):
    root = ScenarioList(None, "Список действий", bot, backend)
    payments = ScenarioList(root, "Платежи", bot, backend)
    CreatePayment(payments, bot, backend)
    ListOwes(payments, bot, backend)
    ListPayments(payments, bot, backend)
    ResolvePayments(payments, bot, backend)
    RemovePayment(payments, bot, backend)
    OweReminder(payments, bot, backend)

    users = ScenarioList(root, "Пользователи", bot, backend)
    RegisterUser(users, bot, backend)
    ListUsers(users, bot, backend)
    ChangeUserName(users, bot, backend)

    restaurants = ScenarioList(root, "Рестораны", bot, backend)
    SelectRandomRestaurant(restaurants, bot, backend)
    RestaurantInviter(restaurants, bot, backend)
    CreateRestaurant(restaurants, bot, backend)
    ListRestaurants(restaurants, bot, backend)
    RemoveRestaurant(restaurants, bot, backend)

    return root
