#!/usr/bin/env python

import db
import logging
import os

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


def test_fill_db(database):
    test_fill_db_users(database)


def test_db_contents(database):
    test_db_contents_users(database)


def test(url):
    logging.basicConfig()
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    with db.Connect(url) as database:
        test_fill_db(database)

    with db.Connect(url) as database:
        test_db_contents(database)


if __name__ == '__main__':
    test_path = '/tmp/db.test.sqlite3'

    if os.path.isfile(test_path):
        os.unlink(test_path)

    test('sqlite:///' + test_path)

