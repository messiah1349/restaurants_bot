from backend import *


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
        , payer=1450
        , creator_id=1451
        , shares={1450: 8000, 1451: 12000}
        , payment_type='other'
        , payment_datetime=None
        , is_resolved=False
        , restaurant_id=None
        , comment="ya malenkaya popka with shares"

    )

    print(resp)


def delete_payment_test(backend):

    print(backend.get_payment_list())

    print(backend.delete_payment(1))
    print(backend.get_payment_list())


if __name__ == '__main__':
    backend = BackEnd(BD_NAME)

    # _ = backend.add_user(1450, 'zhora')
    # _ = backend.add_user(1451, 'stepa')
    #
    # add_payment_test(backend)
    #
    # print(backend.get_payment_list())
    test_add_and_rename_user(backend)



