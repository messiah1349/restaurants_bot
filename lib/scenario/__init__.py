from collections import defaultdict

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

from lib.scenario.mark import (
    ChangeRestaurantMarkScenario,
    ListRestaurantMarks,
    ChangeRestaurantMarkEvent
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

    marks = ScenarioList(root, "Оценки", bot, backend)
    ChangeRestaurantMarkScenario(marks, bot, backend)
    ListRestaurantMarks(marks, bot, backend)

    return root


def init_events(bot, backend):
    subscribers = defaultdict(list)

    def register(event_type, subscriber_type):
        subscribers[event_type].append(subscriber_type(None, bot, backend))

    register("RestaurantMarkChanged", ChangeRestaurantMarkEvent)

    return subscribers
