#!/usr/bin/env python

__all__ = ['Connect']

import datetime
import hashlib
import time

import sqlalchemy  # pip install sqlalchemy
import sqlalchemy.ext.declarative

class Connect:
    """ Context object for Database to support 'with'
    """

    def __init__(self, db_url):
        """
            db - the db to connect to
            cursor - the db cursor, set to return dictionary objects
        """

        self.__db_url = db_url
        self.__db = None

    def __enter__(self):
        """ Start the context (open the storage connection)
        """

        self.__db = Database(self.__db_url)
        return self.__db

    def __exit__(self, exception_type, exception_value, traceback):
        """ End the context (close the db)
            exception_type - type of the exception that was raised. None if no exception
            exception_value - the exception that was raised. None if no exception
            traceback - the stack where the exception was raised. None if no exception
        """

        self.__db.close()


Alchemy_Base = sqlalchemy.ext.declarative.declarative_base()


class Money(sqlalchemy.types.TypeDecorator):
    impl = sqlalchemy.Integer

    def process_bind_param(self, value, dialect):
        return int(value * 100.0 + 0.005)

    def process_result_value(self, value, dialect):
        return value * 100.0


class Date(sqlalchemy.types.TypeDecorator):
    impl = sqlalchemy.types.Date

    def process_bind_param(self, value, dialect):
        try:  # if it is a string, parse it, otherwise it must be datetime object
            return datetime.datetime.strptime(value, "%Y/%m/%d")
        except TypeError:
            return from_user

    def process_result_value(self, value, dialect):
        return value


class User(Alchemy_Base):
    __tablename__ = 'user'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    email = sqlalchemy.Column(sqlalchemy.String(50))
    password_hash = sqlalchemy.Column(sqlalchemy.String(64))

    def __repr__(self):
        return 'User(id=%s, email="%s", password_hash="%s")'%(self.id,
                                                              self.email,
                                                              self.password_hash)

class Bank(Alchemy_Base):
    __tablename__ = 'bank'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String(100))
    url = sqlalchemy.Column(sqlalchemy.String(1024))

    def __repr__(self):
        return 'Bank(id=%s, name="%s", url="%s")'%(self.id, self.name, self.url)


class Account(Alchemy_Base):
    __tablename__ = 'account'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String(100))
    type = sqlalchemy.Column(sqlalchemy.String(5))
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('user.id'))
    user = sqlalchemy.orm.relationship("User", back_populates="accounts")
    bank_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('bank.id'))
    bank = sqlalchemy.orm.relationship("Bank", back_populates="accounts")

    def __repr__(self):
        return ('Account(id=%s, name="%s", ' +
               'type="%s", bank_id=%s, user_id=%s)')%(self.id, self.name, self.type,
                                                    self.bank_id, self.user_id)


User.accounts = sqlalchemy.orm.relationship("Account", order_by=Account.name,
                                            back_populates="user")
Bank.accounts = sqlalchemy.orm.relationship("Account", order_by=Account.name,
                                            back_populates="bank")


class Statement(Alchemy_Base):
    __tablename__ = 'statement'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    start = sqlalchemy.Column(Date)
    end = sqlalchemy.Column(Date)
    fees = sqlalchemy.Column(Money())
    interest = sqlalchemy.Column(Money())
    deposits = sqlalchemy.Column(Money())
    withdrawals = sqlalchemy.Column(Money())
    start_balance = sqlalchemy.Column(Money())
    end_balance = sqlalchemy.Column(Money())
    account_id = sqlalchemy.Column(sqlalchemy.Integer,
                                   sqlalchemy.ForeignKey('account.id'))
    account = sqlalchemy.orm.relationship("Account", back_populates="statements")

    def __repr__(self):
        return ('Statement(id=%s, start="%s", end="%s", fees=$%0.2f, interest=$%0.2f, ' +
               'deposits=$%0.2f, withdrawals=$%0.2f, ' +
               'start_balance=$%0.2f, end_balance=$%0.2f, ' +
               'account_id=%s)')%(self.id, self.start, self.end, self.fees, self.interest,
                                 self.deposits, self.withdrawals,
                                 self.start_balance, self.end_balance, self.account_id)


Account.statements = sqlalchemy.orm.relationship("Statement", order_by=Statement.start,
                                                 back_populates="account")


class Database:

    def __init__(self, db_url):
        self.__db_url = db_url
        self.__engine = sqlalchemy.create_engine(db_url)
        Session = sqlalchemy.orm.sessionmaker(bind=self.__engine)
        self.__session = Session()
        self.__create_tables()

    def __create_tables(self):
        Alchemy_Base.metadata.create_all(self.__engine)

    @staticmethod
    def __hash(text):
        hasher = hashlib.new("sha256")
        hasher.update(text.encode('utf-8'))
        return hasher.hexdigest()

    def engine(self):
        return self.__engine

    def close(self):
        self.__session.commit()
        self.__session.close()

    def add_bank(self, name, url):
        bank = Bank(name=name, url=url)
        self.__session.add(bank)
        return bank

    def list_banks(self):
        return self.__session.query(Bank).all()

    def add_user(self, email, password):
        password_hash = Database.__hash(password)
        user = User(email=email, password_hash=password_hash)
        self.__session.add(user)
        self.__session.commit()
        return user

    def login_user(self, email, password):
        user = self.__session.query(User).filter_by(email=email).one_or_none()
        if not user:
            return User(email=email)
        password_hash = Database.__hash(password)
        if password_hash != user.password_hash:
            return User(email=email, password_hash=password_hash)
        return user

    def add_account(self, user, bank, account_name, account_type):
        account = Account(user=user, bank=bank, name=account_name, type=account_type)
        self.__session.add(account)
        return account

    def list_accounts(self, user, account_type):
        return self.__session.query(Account).filter_by(user=user, type=account_type).all()

    def add_statement(self, account, start, end, fees, interest, deposits,
                      withdrawals, start_balance, end_balance):
        statement = Statement(account=account,
                              start=start, end=end,
                              fees=fees, interest=interest,
                              deposits=deposits, withdrawals=withdrawals,
                              start_balance=start_balance, end_balance=end_balance)
        self.__session.add(statement)
        return statement

    def list_statements(self, account, limit):
        return self.__session.query(Statement).filter_by(account=account
                                                         ).limit(limit).all()


def test_values(database):
    banks = database.list_banks()
    if len(banks) != 2:
        raise SyntaxError("Banks found (expected 2): " + str(banks))
    results = database.login_user('them@me.com', 'secret')
    if results.id or results.password_hash:
        raise SyntaxError('Unexpected pass: ' + str(results))

    boa = [bank for bank in banks if bank.name == 'Bank of America']
    if len(boa) != 1:
        raise SyntaxError('We do not have just one boa: ' + str(boa))

    myself = database.login_user('me@me.com', 'secret')
    if not myself.id or not myself.password_hash:
        raise SyntaxError('Unexpected fail: ' + str(myself))
    results = database.login_user('me@me.com', 'toomanysecrets')
    if results.id or not results.password_hash:
        raise SyntaxError('Unexpected value: ' + str(results))
    you = database.login_user('u@me.com', 'toomanysecrets')
    if not you.id or not you.password_hash:
        raise SyntaxError('Unexpected fail: ' + str(you))

    me_accounts = database.list_accounts(myself, 'cc')
    if len(me_accounts) != 2:
        raise SyntaxError("Accounts (me) found (expected 2 cc): " + str(me_accounts))

    my_boa_cc = [account for account in me_accounts if account.bank == boa[0]]
    if len(my_boa_cc) != 1:
        raise SyntaxError('We do not have just one boa cc: ' + str(my_boa_cc))
    my_boa_cc_statements = database.list_statements(my_boa_cc[0], 1)
    if len(my_boa_cc_statements) != 1:
        raise SyntaxError('We limited statements to 1 but got: '
                          + str(my_boa_cc_statements))
    my_boa_cc_statements = database.list_statements(my_boa_cc[0], 100)
    if len(my_boa_cc_statements) != 2:
        raise SyntaxError('We should have 2 boa cc statements but got: '
                          + str(my_boa_cc_statements))

    me_accounts = database.list_accounts(myself, 'ch')
    if len(me_accounts) != 1:
        raise SyntaxError("Accounts (me) found (expected 1 ch): " + str(me_accounts))

    my_boa_ch = [account for account in me_accounts if account.bank == boa[0]]
    if len(my_boa_cc) != 1:
        raise SyntaxError('We do not have just one boa ch: ' + str(my_boa_cc))
    my_boa_ch_statements = database.list_statements(my_boa_ch[0], 100)
    if len(my_boa_ch_statements) != 1:
        raise SyntaxError('We should have 1 boa ch statement but got: '
                          + str(my_boa_ch_statements))

    me_accounts = database.list_accounts(myself, 'inv')
    if me_accounts:
        raise SyntaxError("Accounts (me) found (expected 0 inv): " + str(me_accounts))

    me_accounts = database.list_accounts(myself, 'mort')
    if me_accounts:
        raise SyntaxError("Accounts (me) found (expected 0 mort): " + str(me_accounts))

    you_accounts = database.list_accounts(you, 'cc')
    if len(you_accounts) != 1:
        raise SyntaxError("Accounts (you) found (expected 1 cc): " + str(you_accounts))

    you_accounts = database.list_accounts(you, 'ch')
    if you_accounts:
        raise SyntaxError("Accounts (you) found (expected 0 ch): " + str(you_accounts))

    you_accounts = database.list_accounts(you, 'inv')
    if len(you_accounts) != 1:
        raise SyntaxError("Accounts (you) found (expected 1 inv): " + str(you_accounts))

    your_boa_inv = [account for account in you_accounts
                    if account.bank == boa[0]]
    if len(your_boa_inv) != 1:
        raise SyntaxError('We do not have just one boa inv: ' + str(your_boa_inv))
    your_boa_inv_statements = database.list_statements(your_boa_inv[0], 100)
    if len(your_boa_inv_statements) != 1:
        raise SyntaxError('We should have 1 boa inv statement but got: '
                          + str(your_boa_inv_statements))

    you_accounts = database.list_accounts(you, 'mort')
    if len(you_accounts) != 1:
        raise SyntaxError("Accounts (you) found (expected 1 mort): " + str(you_accounts))
    # TODO: Test statements


def fill_db(database):
    boa = database.add_bank('Bank of America', 'https://BankOfAmerica.com/')
    citi = database.add_bank('CitiBank', 'https://citi.com/')

    myself = database.add_user('me@me.com', 'secret')
    you = database.add_user('u@me.com', 'toomanysecrets')

    boa_cc = database.add_account(myself, boa, 'Credit Card', 'cc')
    boa_checking = database.add_account(myself, boa, 'Checking', 'ch')
    citi_cc = database.add_account(myself, citi, 'Credit Card', 'cc')

    boa_investing = database.add_account(you, boa, 'Investment', 'inv')
    citi_mortgage = database.add_account(you, citi, 'Mortgage', 'mort')
    citi_cc = database.add_account(you, citi, 'Credit Card', 'cc')

    s1 = database.add_statement(boa_cc, '2019/09/01', '2019/09/30',
                                3.56, 17.55, 138.56, 88.12, 156.77, 207.21)
    s2 = database.add_statement(boa_cc, '2019/08/01', '2019/08/31',
                                2.56, 16.55, 137.56, 87.12, 155.77, 206.21)
    s3 = database.add_statement(boa_checking, '2019/07/01', '2019/07/31',
                                1.56, 15.55, 136.56, 86.12, 154.77, 205.21)

    s4 = database.add_statement(boa_investing, '2019/07/01', '2019/07/31',
                                1.56, 15.55, 136.56, 86.12, 154.77, 205.21)


def clear_db(database):
    Statement.__table__.drop(database.engine())
    Account.__table__.drop(database.engine())
    Bank.__table__.drop(database.engine())
    User.__table__.drop(database.engine())


def test(url):
    import datetime
    import logging

    logging.basicConfig()
    #logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    with Connect(url) as database:
        fill_db(database)
        test_values(database)

    with Connect(url) as database:
        test_values(database)

    with Connect(url) as database:
        clear_db(database)


if __name__ == '__main__':
    test('sqlite:////tmp/db.test.sqlite3')
    #test('mysql+mysqlconnector://marcp:p455w0rd@localhost/game')

"""
brew install mysql
brew services start mysql
mysql_secure_installation
mysql -uroot -p
> CREATE USER 'newuser'@'localhost' IDENTIFIED BY 'password';
> GRANT ALL PRIVILEGES ON * . * TO 'newuser'@'localhost';
mysql -u newuser -p
> CREATE DATABASE dbname;
> user dbname;
"""
