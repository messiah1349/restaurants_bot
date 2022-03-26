import sys
sys.path.append('../lib/')

from collections import Counter
from backend import *
BD_NAME = '../data/prod.db'


def test_add_and_rename_user(backend):

    backend._test()
    # backend._check_user_by_id('aasd')
    print('add kac')
    resp = backend.add_user(1489, 'kac')
    print(resp)

    user_list = backend.get_users_list()
    print(user_list)

    print('wrong rename')
    resp = backend.change_user_name(1485, 'varlamov')
    print(resp)
    user_list = backend.get_users_list()
    print(user_list)

    print('true rename')
    resp = backend.change_user_name(1489, 'varlamov')
    user_list = backend.get_users_list()
    print(user_list)

    print('wrong remove')
    resp = backend.remove_user(1500)
    print(resp)

    print('true remove')
    resp = backend.remove_user(1489)
    print(resp)

    user_list = backend.get_users_list()
    print(user_list)


def add_payment_test(backend):

    resp = backend.add_payment(
        total=20000
        , payer=46340594
        , creator_id=46340594
        , shares={114768813: 8000, 46340594: 12000}
        , payment_type='other'
        , payment_datetime=None
        , is_resolved=False
        , restaurant_id=None
        , comment="zalupke"

    )
    print(resp)

    resp = backend.add_payment(
        total=30000
        , payer=46340594
        , creator_id=46340594
        , shares={114768813: 8000, 46340594: 22000}
        , payment_type='other'
        , payment_datetime=None
        , is_resolved=False
        , restaurant_id=None
        , comment="zalupke2"

    )
    print(resp)


def delete_payment_test(backend):

    print(backend.get_payment_list())

    print(backend.delete_payment(12))
    print(backend.delete_payment(13))
    print(backend.get_payment_list())


def check_rest_get_probs(backend):
    names = ['plennica', 'taverna2', 'beirut']
    prs = [0.625, 1, 0.75]
    print({name: pr / sum(prs) for name, pr in zip(names, prs)})

    cnt = Counter()
    n = 10000
    for i in range(n):
        ans = backend.get_random_restaurant().answer
        top_ans = ans[0]['restaurant_name']
        cnt.update([top_ans])

    print({rest: float(val) / n for rest, val in cnt.items()})

if __name__ == '__main__':
    backend = Backend(BD_NAME)
    # backend._execute_query('drop table restaurant_mark')



    # print(backend.add_restaurant('beirut'))


    print(backend.add_restaurant_mark(2, 46340594, 'Очень хочу'))
    print(backend.add_restaurant_mark(2, 114768813, 'Не хотелось бы'))
    print(backend.add_restaurant_mark(3, 46340594, 'Ужасно'))
    print(backend.add_restaurant_mark(3, 46340594, 'Очень хочу'))
    print(backend.add_restaurant_mark(3, 114768813, 'Очень хочу'))
    print(backend.add_restaurant_mark(4, 46340594, 'Очень хочу'))
    print(backend.add_restaurant_mark(4, 46340594, 'Хуй'))

    check_rest_get_probs(backend)


    # print(backend.get_restaurant_list())
    # print(backend.add_restaurant('taverna2'))
    # print(backend.get_restaurant_list())
    # print(backend.remove_restaurant(1))
    # print(backend.get_restaurant_list())
    # delete_payment_test(backend)
    # add_payment_test(backend)

    # backend.add_restaurant('plennica')

    # print(backend.get_payment_list())

    # backend.resolve(1450)
    # print(backend.get_owes())

    # test_add_and_rename_user(backend)

    # _ = backend.add_user(1450, 'zhora')
    # _ = backend.add_user(1451, 'stepa')
    #
    # add_payment_test(backend)
    #
    # print(backend.get_payment_list())
    # delete_payment_test(backend)
    # add_payment_test(backend)


