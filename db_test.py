#!/usr/bin/env python

import db
import logging
import os
import datetime

def test_fill_db_users(database):
    myself = database.add_user('me@me.com', 'secret')
    you = database.add_user('u@me.com', 'toomanysecrets')


def test_db_contents_users(database):
    myself = database.login_user('me@me.com', 'toomanysecrets')

    if myself['id'] == None or myself['valid'] or myself['email'] != 'me@me.com':
        raise SyntaxError('logging myself in passed but should not have: '
                          + str(myself))

    myself = database.login_user('me@me.com', 'secret')

    if myself['id'] == None or not myself['valid'] or myself['email'] != 'me@me.com':
        raise SyntaxError('logging me in failed: ' + str(myself))

    you = database.login_user('u@me.com', 'toomanysecrets')

    if you['id'] == None or not you['valid'] or you['email'] != 'u@me.com':
        raise SyntaxError('logging me in failed: ' + str(you))

    other = database.login_user('other@me.com', 'halls pass')

    if other['id'] != None or other['valid'] or other['email'] != 'other@me.com':
        raise SyntaxError('logging other in passed and should not have: ' + str(other))


def test_fill_db_accounts(database):
    myself = database.login_user('me@me.com', 'secret')
    you = database.login_user('u@me.com', 'toomanysecrets')

    my_bank_account = database.add_account(myself['id'],
                                           'bank savings',
                                           'http://bank.com/',
                                           'usual login',
                                           'SAVE')
    my_cc = database.add_account(myself['id'],
                                 'bank visa',
                                 'http://bank.com/',
                                 'usual login',
                                 'CC')
    my_house = database.add_account(myself['id'],
                                    'home',
                                    'http://zillow.com/',
                                    'address',
                                    'HOUSE')
    my_mortgage = database.add_account(myself['id'],
                                    'home mortgage',
                                    'http://morgage.com/',
                                    'account id',
                                    'MORT',
                                    my_house['id'])

    your_cc = database.add_account(you['id'],
                                 'bank mastercard',
                                 'http://creditunion.org/',
                                 'usual login',
                                 'CC')


def test_db_contents_accounts(database):
    myself = database.login_user('me@me.com', 'secret')
    you = database.login_user('u@me.com', 'toomanysecrets')
    my_accounts = database.list_accounts(myself['id'])
    your_accounts = database.list_accounts(you['id'])

    if len(my_accounts) != 4:
        raise SyntaxError('my accounts count was wrong, expected 4, got '
                          + str(len(my_accounts)))

    if len(your_accounts) != 1:
        raise SyntaxError('your accounts count was wrong, expected 1, got '
                          + str(len(your_accounts)))

    if (your_accounts[0]['name'] != 'bank mastercard'
        or your_accounts[0]['url'] != 'http://creditunion.org/'
        or your_accounts[0]['info'] != 'usual login'
        or your_accounts[0]['type'] != 'CC'):
        raise SyntaxError('your account was not what we expected: '
                          + str(your_accounts[0]))

    my_cc = [x for x in my_accounts if x['type'] == 'CC']

    if len(my_cc) != 1:
        raise SyntaxError('Looked for 1 CC but found: ' + str(my_cc))

    if (my_cc[0]['name'] != 'bank visa'
        or my_cc[0]['url'] != 'http://bank.com/'
        or my_cc[0]['info'] != 'usual login'):
        raise SyntaxError('my CC account was not what we expected: '
                          + str(my_cc[0]))

    my_savings = [x for x in my_accounts if x['type'] == 'SAVE']

    if len(my_savings) != 1:
        raise SyntaxError('Looked for 1 savings account but found: '
                          + str(my_savings))

    if (my_savings[0]['name'] != 'bank savings'
        or my_savings[0]['url'] != 'http://bank.com/'
        or my_savings[0]['info'] != 'usual login'):
        raise SyntaxError('my savings account was not what we expected: '
                          + str(my_savings[0]))

    my_house = [x for x in my_accounts if x['type'] == 'HOUSE']

    if len(my_house) != 1:
        raise SyntaxError('Looked for 1 house but found: '
                          + str(my_house))

    if (my_house[0]['name'] != 'home'
        or my_house[0]['url'] != 'http://zillow.com/'
        or my_house[0]['info'] != 'address'):
        raise SyntaxError('my house was not what we expected: '
                          + str(my_house[0]))

    my_mortgage = [x for x in my_accounts if x['type'] == 'MORT']

    if len(my_mortgage) != 1:
        raise SyntaxError('Looked for 1 house but found: '
                          + str(my_mortgage))

    if (my_mortgage[0]['name'] != 'home mortgage'
        or my_mortgage[0]['url'] != 'http://morgage.com/'
        or my_mortgage[0]['info'] != 'account id'):
        raise SyntaxError('my house was not what we expected: '
                          + str(my_mortgage[0]))

    if my_mortgage[0]['asset_id'] != my_house[0]['id']:
        raise SyntaxError('mortgage asset id (%s) does not match house id (%s)'%(
                          my_mortgage[0]['asset_id'], my_house[0]['id']))


def test_fill_db_statements(database):
    myself = database.login_user('me@me.com', 'secret')
    you = database.login_user('u@me.com', 'toomanysecrets')

    my_accounts = database.list_accounts(myself['id'])
    your_accounts = database.list_accounts(you['id'])

    my_savings = [x for x in my_accounts if x['type'] == 'SAVE'][0]
    my_cc = [x for x in my_accounts if x['type'] == 'CC'][0]
    my_house = [x for x in my_accounts if x['type'] == 'HOUSE'][0]
    my_mortgage = [x for x in my_accounts if x['type'] == 'MORT'][0]
    your_cc = [x for x in your_accounts if x['type'] == 'CC'][0]

    database.add_statement(my_savings['id'],
                           '2020/06/01', '2020/06/30',
                           3.11, 1.13, 123.45, 456.78, 1000.00, 664.69)
    database.add_statement(my_savings['id'],
                           '2020/05/01', '2020/05/31',
                           3.11, 1.13, 123.45, 456.78, 1335.31, 1000.00)


def test_db_contents_statements(database):
    myself = database.login_user('me@me.com', 'secret')
    you = database.login_user('u@me.com', 'toomanysecrets')

    my_accounts = database.list_accounts(myself['id'])
    your_accounts = database.list_accounts(you['id'])

    my_savings = [x for x in my_accounts if x['type'] == 'SAVE'][0]
    my_cc = [x for x in my_accounts if x['type'] == 'CC'][0]
    my_house = [x for x in my_accounts if x['type'] == 'HOUSE'][0]
    my_mortgage = [x for x in my_accounts if x['type'] == 'MORT'][0]
    your_cc = [x for x in your_accounts if x['type'] == 'CC'][0]

    my_savings_statements = database.list_statements(my_savings['id'])

    if len(my_savings_statements) != 2:
        raise SyntaxError('Number of my savings statements expected 2 but found '
                          + str(len(my_savings_statements)))

    may_statement = [s for s in my_savings_statements
                     if s['start'] == datetime.date(2020, 5, 1)]

    if len(may_statement) != 1:
        raise SyntaxError('May statement count is off, expected 1 got '
                          + str(len(may_statement)))

    if (may_statement[0]['end'] != datetime.date(2020, 5, 31)
        or may_statement[0]['fees'] != 3.11
        or may_statement[0]['deposits'] != 123.45
        or may_statement[0]['withdrawals'] != 456.78
        or may_statement[0]['start_balance'] != 1335.31
        or may_statement[0]['end_balance'] != 1000.00
        or may_statement[0]['interest'] != 1.13):
        raise SyntaxError('May statement is not what we expected: '
                          + str(may_statement[0]))

    june_statement = [s for s in my_savings_statements
                     if s['start'] == datetime.date(2020, 6, 1)]

    if len(june_statement) != 1:
        raise SyntaxError('June statement count is off, expected 1 got '
                          + str(len(june_statement)))

    if (june_statement[0]['end'] != datetime.date(2020, 6, 30)
        or june_statement[0]['fees'] != 3.11
        or june_statement[0]['deposits'] != 123.45
        or june_statement[0]['withdrawals'] != 456.78
        or june_statement[0]['start_balance'] != 1000.00
        or june_statement[0]['end_balance'] != 664.69
        or june_statement[0]['interest'] != 1.13):
        raise SyntaxError('June statement is not what we expected: '
                          + str(june_statement[0]))


def test_fill_db(database):
    test_fill_db_users(database)
    test_fill_db_accounts(database)
    test_fill_db_statements(database)


def test_db_contents(database):
    test_db_contents_users(database)
    test_db_contents_accounts(database)
    test_db_contents_statements(database)


def test(url):
    logging.basicConfig()
    #logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    with db.Connect(url) as database:
        test_fill_db(database)

    with db.Connect(url) as database:
        test_db_contents(database)


if __name__ == '__main__':
    test_path = '/tmp/db.test.sqlite3'

    if os.path.isfile(test_path):
        os.unlink(test_path)

    test('sqlite:///' + test_path)

