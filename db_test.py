#!/usr/bin/env python3

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
                                    4.1,
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
        or my_mortgage[0]['interest_rate'] != 4.1
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
                           '2020/06/01', '2020/06/30', '2020/07/14',
                           3.11, 1.13, 123.45, 456.78, 1000.00, 664.69)
    database.add_statement(my_savings['id'],
                           '2020/05/01', '2020/05/31', None,
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
        or may_statement[0]['due'] != None
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
        or june_statement[0]['due'] != datetime.date(2020, 7, 14)
        or june_statement[0]['fees'] != 3.11
        or june_statement[0]['deposits'] != 123.45
        or june_statement[0]['withdrawals'] != 456.78
        or june_statement[0]['start_balance'] != 1000.00
        or june_statement[0]['end_balance'] != 664.69
        or june_statement[0]['interest'] != 1.13):
        raise SyntaxError('June statement is not what we expected: '
                          + str(june_statement[0]))


def test_fill_db_feedback(database):
    myself = database.login_user('me@me.com', 'secret')
    you = database.login_user('u@me.com', 'toomanysecrets')

    f1 = database.add_feedback(myself['id'], 'BUG', 'error', 'error when I do stuff')
    f2 = database.add_feedback(you['id'], 'BUG', 'error', 'error when I do stuff')
    f3 = database.add_feedback(you['id'], 'REQUEST', 'auto report errors', 'why users')
    f4 = database.add_feedback(myself['id'], 'REQUEST', 'errors ui', 'users can see')
    database.relate_feedback(f1['id'], f2['id'], 'duplicate', 'duplicate')
    database.relate_feedback(f1['id'], f3['id'], 'related', 'related')
    database.relate_feedback(f2['id'], f3['id'], 'related', 'related')
    database.relate_feedback(f3['id'], f4['id'], 'predecessor', 'successor')
    database.feedback_vote(myself['id'], f1['id'], 10)
    database.feedback_vote(myself['id'], f2['id'], 20)
    database.feedback_vote(myself['id'], f3['id'], 30)
    database.feedback_vote(myself['id'], f4['id'], 40)
    database.feedback_vote(you['id'], f1['id'], 100)
    database.feedback_vote(you['id'], f2['id'], 200)
    database.feedback_vote(you['id'], f3['id'], 300)


def test_db_contents_feedback(database):
    myself = database.login_user('me@me.com', 'secret')
    you = database.login_user('u@me.com', 'toomanysecrets')

    my_feedback = database.list_feedback(myself['id'])
    my_bug = [x for x in my_feedback if x['type'] == 'BUG']
    my_request = [x for x in my_feedback if x['type'] == 'REQUEST']
    your_feedback = database.list_feedback(you['id'])
    your_bug = [x for x in your_feedback if x['type'] == 'BUG']
    your_request = [x for x in your_feedback if x['type'] == 'REQUEST']

    if len(my_feedback) != 2:
        raise SyntaxError('Expected 2 feedback but got %d'%(len(my_feedback)))

    if len(my_bug) != 1:
        raise SyntaxError('Expected 1 bug feedback but got %d'%(len(my_bug)))

    if len(my_request) != 1:
        raise SyntaxError('Expected 1 request feedback but got %d'%(len(my_request)))

    if (my_bug[0]['type'] != 'BUG'
        or my_bug[0]['subject'] != 'error'
        or my_bug[0]['description'] != 'error when I do stuff'):
        raise SyntaxError('feedback was not as we expected: ' + str(my_bug))

    if (my_request[0]['type'] != 'REQUEST'
        or my_request[0]['subject'] != 'errors ui'
        or my_request[0]['description'] != 'users can see'):
        raise SyntaxError('feedback was not as we expected: ' + str(my_request))

    if len(your_feedback) != 2:
        raise SyntaxError('Expected 2 feedback but got %d'%(len(your_feedback)))

    if len(your_bug) != 1:
        raise SyntaxError('Expected 1 bug feedback but got %d'%(len(your_bug)))

    if len(your_request) != 1:
        raise SyntaxError('Expected 1 request feedback but got %d'%(len(your_request)))

    if (your_bug[0]['type'] != 'BUG'
        or your_bug[0]['subject'] != 'error'
        or your_bug[0]['description'] != 'error when I do stuff'):
        raise SyntaxError('feedback was not as we expected: ' + str(your_bug))

    if (your_request[0]['type'] != 'REQUEST'
        or your_request[0]['subject'] != 'auto report errors'
        or your_request[0]['description'] != 'why users'):
        raise SyntaxError('feedback was not as we expected: ' + str(your_request))

    my_bug_related = database.list_related_feedback(my_bug[0]['id'])
    my_request_related = database.list_related_feedback(my_request[0]['id'])
    your_bug_related = database.list_related_feedback(your_bug[0]['id'])
    your_request_related = database.list_related_feedback(your_request[0]['id'])

    if len(my_bug_related) != 2:
        raise SyntaxError('We expected 2 related but got %d'%(len(my_bug_related)))

    if len(my_request_related) != 1:
        raise SyntaxError('We expected 1 related but got %d'%(len(my_request_related)))

    if len(your_bug_related) != 2:
        raise SyntaxError('We expected 2 related but got %d'%(len(your_bug_related)))

    if len(your_request_related) != 3:
        raise SyntaxError('We expected 3 related but got' +
                          ' %d'%(len(your_request_related)))

    my_bug_related_duplicate = [x for x in my_bug_related
                                if x['to_type'] == 'duplicate']
    my_bug_related_related = [x for x in my_bug_related
                              if x['to_type'] == 'related']
    your_bug_related_duplicate = [x for x in your_bug_related
                                  if x['to_type'] == 'duplicate']
    your_bug_related_related = [x for x in your_bug_related
                                if x['to_type'] == 'related']
    your_request_related_successor = [x for x in your_request_related
                                      if x['to_type'] == 'successor']
    your_request_related_my_bug = [x for x in your_request_related
                                   if x['from_id'] == my_bug[0]['id']]
    your_request_related_your_bug = [x for x in your_request_related
                                     if x['from_id'] == your_bug[0]['id']]

    if len(my_bug_related_duplicate) != 1:
        raise SyntaxError('We expected 1 related but got' +
                          ' %d'%(len(my_bug_related_duplicate)))

    if len(my_bug_related_related) != 1:
        raise SyntaxError('We expected 1 related but got' +
                          ' %d'%(len(my_bug_related_related)))

    if len(your_bug_related_duplicate) != 1:
        raise SyntaxError('We expected 1 related but got' +
                          ' %d'%(len(your_bug_related_duplicate)))

    if len(your_bug_related_related) != 1:
        raise SyntaxError('We expected 1 related but got' +
                          ' %d'%(len(your_bug_related_related)))

    if len(your_request_related_successor) != 1:
        raise SyntaxError('We expected 1 related but got' +
                          ' %d'%(len(your_request_related_successor)))

    if len(your_request_related_my_bug) != 1:
        raise SyntaxError('We expected 1 related but got' +
                          ' %d'%(len(your_request_related_my_bug)))

    if len(your_request_related_your_bug) != 1:
        raise SyntaxError('We expected 1 related but got' +
                          ' %d'%(len(your_request_related_your_bug)))

    my_bug_votes = database.feedback_all_votes(my_bug[0]['id'])
    my_request_votes = database.feedback_all_votes(my_request[0]['id'])
    your_bug_votes = database.feedback_all_votes(your_bug[0]['id'])
    your_request_votes = database.feedback_all_votes(your_request[0]['id'])
    my_vote_my_bug = database.feedback_vote(myself['id'], my_bug[0]['id'])
    my_vote_my_request = database.feedback_vote(myself['id'], my_request[0]['id'])
    my_vote_your_bug = database.feedback_vote(myself['id'], your_bug[0]['id'])
    my_vote_your_request = database.feedback_vote(myself['id'], your_request[0]['id'])
    your_vote_my_bug = database.feedback_vote(you['id'], my_bug[0]['id'])
    your_vote_my_request = database.feedback_vote(you['id'], my_request[0]['id'])
    your_vote_your_bug = database.feedback_vote(you['id'], your_bug[0]['id'])
    your_vote_your_request = database.feedback_vote(you['id'], your_request[0]['id'])

    if my_vote_my_bug['votes'] != 10:
        raise SyntaxError('Expected 10 but got %d'%(my_vote_my_bug['votes']))

    if my_vote_my_request['votes'] != 40:
        raise SyntaxError('Expected 40 but got %d'%(my_vote_my_request['votes']))

    if my_vote_your_bug['votes'] != 20:
        raise SyntaxError('Expected 20 but got %d'%(my_vote_your_bug['votes']))

    if my_vote_your_request['votes'] != 30:
        raise SyntaxError('Expected 30 but got %d'%(my_vote_your_request['votes']))

    if your_vote_my_bug['votes'] != 100:
        raise SyntaxError('Expected 100 but got %d'%(your_vote_my_bug['votes']))

    if your_vote_my_request['votes'] != 0:
        raise SyntaxError('Expected 0 but got %d'%(your_vote_my_request['votes']))

    if your_vote_your_bug['votes'] != 200:
        raise SyntaxError('Expected 200 but got %d'%(your_vote_your_bug['votes']))

    if your_vote_your_request['votes'] != 300:
        raise SyntaxError('Expected 300 but got %d'%(your_vote_your_request['votes']))

    if sum([x['votes'] for x in my_bug_votes]) != 110:
        raise SyntaxError('Expected 110 but got ' +
                          '%d'%(sum([x['votes'] for x in my_bug_votes])))

    if sum([x['votes'] for x in my_request_votes]) != 40:
        raise SyntaxError('Expected 40 but got ' +
                          '%d'%(sum([x['votes'] for x in my_request_votes])))

    if sum([x['votes'] for x in your_bug_votes]) != 220:
        raise SyntaxError('Expected 220 but got ' +
                          '%d'%(sum([x['votes'] for x in your_bug_votes])))

    if sum([x['votes'] for x in your_request_votes]) != 330:
        raise SyntaxError('Expected 330 but got ' +
                          '%d'%(sum([x['votes'] for x in your_request_votes])))


def test_fill_db_points(database):
    myself = database.login_user('me@me.com', 'secret')
    you = database.login_user('u@me.com', 'toomanysecrets')

    database.user_points(myself['id'], 1, 'daily visit')
    database.user_points(myself['id'], 10, 'debt free')
    database.user_points(you['id'], 5, 'emergency funded')
    database.user_points(you['id'], 20, 'yep')


def test_db_contents_points(database):
    myself = database.login_user('me@me.com', 'secret')
    you = database.login_user('u@me.com', 'toomanysecrets')

    my_points = database.user_points(myself['id'])
    your_points = database.user_points(you['id'])

    if len(my_points) != 2:
        raise SyntaxError('Expected 2 but got %d'%(len(my_points)))

    if len(your_points) != 2:
        raise SyntaxError('Expected 2 but got %d'%(len(your_points)))

    my_point_value = sum([x['awarded'] for x in my_points])
    your_point_value = sum([x['awarded'] for x in your_points])

    if my_point_value != 11:
        raise SyntaxError('Expected 11 but got %d'%(my_point_value))

    if your_point_value != 25:
        raise SyntaxError('Expected 25 but got %d'%(your_point_value))

    my_daily_visit = [x for x in my_points if x['reason'] == 'daily visit']
    my_debt_free = [x for x in my_points if x['reason'] == 'debt free']
    your_emergency = [x for x in your_points if x['reason'] == 'emergency funded']
    your_yep = [x for x in your_points if x['reason'] == 'yep']

    if len(my_daily_visit) != 1:
        raise SyntaxError('Expected 1 but got %d'%(len(my_daily_visit)))

    if len(my_debt_free) != 1:
        raise SyntaxError('Expected 1 but got %d'%(len(my_debt_free)))

    if len(your_emergency) != 1:
        raise SyntaxError('Expected 1 but got %d'%(len(your_emergency)))

    if len(your_yep) != 1:
        raise SyntaxError('Expected 1 but got %d'%(len(your_yep)))


def test_fill_db(database):
    test_fill_db_users(database)
    test_fill_db_accounts(database)
    test_fill_db_statements(database)
    test_fill_db_feedback(database)
    test_fill_db_points(database)


def test_db_contents(database):
    test_db_contents_users(database)
    test_db_contents_accounts(database)
    test_db_contents_statements(database)
    test_db_contents_feedback(database)
    test_db_contents_points(database)


def test(url):
    logging.basicConfig()
    #logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    with db.Connect(url) as database:
        test_fill_db(database)

    with db.Connect(url) as database:
        test_db_contents(database)


def sqlite_new_file(path):
    if os.path.isfile(path):
        os.unlink(path)

    return 'sqlite:///' + path


if __name__ == '__main__':
    test(sqlite_new_file('/tmp/db.test.sqlite3'))

