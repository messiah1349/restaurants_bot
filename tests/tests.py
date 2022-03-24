import sys
sys.path.append('../lib/')

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


if __name__ == '__main__':
    backend = Backend(BD_NAME)

    print (backend.get_restaurant_mark_list())
    print(backend.add_restaurant_mark(1, 46340594, 'zbs'))
    print (backend.get_restaurant_mark_list())
    print(backend.add_restaurant_mark(1, 114768813, 'zbs2'))
    print (backend.get_restaurant_mark_list())
    print(backend.add_restaurant_mark(1, 46340594, 'huynya'))
    print (backend.get_restaurant_mark_list())



    # print(backend.get_restaurant_list())
    # print(backend.add_restaurant('taverna'))
    # print(backend.get_restaurant_list())
    # print(backend.remove_restaurant(1))
    # print(backend.get_restaurant_list())
    # delete_payment_test(backend)
    # add_payment_test(backend)



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


