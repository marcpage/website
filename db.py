#!/usr/bin/env python


__all__ = ['Connect']


import sqlalchemy
import sqlalchemy.ext.declarative
import threading
import queue
import logging
import hashlib
import traceback
import datetime

# TODO: Change user info
# TODO: Change account info

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

    @staticmethod
    def hash(text):
        hasher = hashlib.new('sha256')
        hasher.update(text.encode('utf-8'))
        return hasher.hexdigest()

    def set_password(self, password):
        hasher = hashlib.new('sha256')
        hasher.update(text.encode('utf-8'))
        password_hash = User.hash(password)

    def password_matches(self, password):
        return User.hash(password) == self.password_hash

    def __repr__(self):
        return 'User(id=%s, email="%s", password_hash="%s")'%(self.id,
                                                              self.email,
                                                              self.password_hash)


class Account(Alchemy_Base):
    __tablename__ = 'account'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String(100))
    url = sqlalchemy.Column(sqlalchemy.String(1024))
    info = sqlalchemy.Column(sqlalchemy.String(4096))
    type = sqlalchemy.Column(sqlalchemy.String(5))
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('user.id'))
    user = sqlalchemy.orm.relationship('User', backref='accounts')
    asset_id = sqlalchemy.Column(sqlalchemy.Integer,
                                 sqlalchemy.ForeignKey('account.id'))
    asset = sqlalchemy.orm.relationship('Account')
    debts = sqlalchemy.orm.relationship('Account', remote_side=[id])

    def __repr__(self):
        return ('Account(id=%s, name="%s", ' +
               'type="%s", url="%s", info="%s", ' +
               ' user_id=%s, asset_id=%s)')%(self.id, self.name, self.type,
                                             self.url, self.info, self.user_id,
                                             self.asset_id)


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
    account = sqlalchemy.orm.relationship("Account", backref="statements")

    def __repr__(self):
        return ('Statement(id=%s, start="%s", end="%s", ' +
                'fees=$%0.2f, interest=$%0.2f, ' +
                'deposits=$%0.2f, withdrawals=$%0.2f, ' +
                'start_balance=$%0.2f, end_balance=$%0.2f, ' +
                'account_id=%s)')%(self.id, self.start, self.end,
                                 self.fees if self.fees else -1,
                                 self.interest if self.interest else -1,
                                 self.deposits if self.deposits else -1,
                                 self.withdrawals if self.withdrawals else -1,
                                 self.start_balance if self.start_balance else -1,
                                 self.end_balance if self.end_balance else -1,
                                 self.account_id)


class Connect(threading.Thread):

    def __init__(self, url):
        self.__url = url
        self.__running = True
        self.__q = queue.Queue()
        threading.Thread.__init__(self)
        self.daemon= False
        self.start()

    def __enter__(self):
        """ Start the context (open the storage connection)
        """
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """ End the context (close the db)
            exception_type - type of the exception that was raised. None if no exception
            exception_value - the exception that was raised. None if no exception
            traceback - the stack where the exception was raised. None if no exception
        """
        self.close()

    def close(self):
        self.__q.put(None)
        self.join()

    def __init(self):
        engine = sqlalchemy.create_engine(self.__url)
        factory = sqlalchemy.orm.sessionmaker(bind=engine)
        Session = sqlalchemy.orm.scoped_session(factory)
        self.__session = Session()
        Alchemy_Base.metadata.create_all(engine)
        return engine

    def __add(self, object):
        self.__session.add(object)
        self.__session.commit()
        return object

    def __find_user(self, email):
        return self.__session.query(User).filter(sqlalchemy.func.lower(User.email)
                                                 == sqlalchemy.func.lower(email)
                                                 ).one_or_none()

    def add_user(self, email, password):
        results = queue.Queue()
        self.__q.put(('user','add',results, email, password))
        return results.get()

    def login_user(self, email, password):
        results = queue.Queue()
        self.__q.put(('user','login',results, email, password))
        return results.get()

    def add_account(self, user_id, name, url, info, type, asset_id=None):
        results = queue.Queue()
        self.__q.put(('account','add', results, user_id, name, url, info,
                      type, asset_id))
        return results.get()

    def list_accounts(self, user_id):
        results = queue.Queue()
        self.__q.put(('account','list', results, user_id))
        return results.get()

    def add_statement(self, account_id, start, end,
                      fees, interest, deposits, withdrawals,
                      start_balance, end_balance):
        results = queue.Queue()
        self.__q.put(('statement','add', results, account_id,  start, end,
                      fees, interest, deposits, withdrawals,
                      start_balance, end_balance))
        return results.get()

    def list_statements(self, account_id):
        results = queue.Queue()
        self.__q.put(('statement','list', results, account_id))
        return results.get()

    def __add_user(self, email, password):
        user = self.__find_user(email=email)

        if user:
            return ({'id': None, 'valid': False})

        else:
            password_hash = password_hash=User.hash(password)
            user = self.__add(User(email=email,
                                   password_hash=password_hash))
            return ({'id': user.id,
                            'email': email,
                            'valid': True})

    def __login_user(self, email, password):
        user = self.__find_user(email=email)

        if not user:
            return ({'id': None,
                            'email': email,
                            'valid': False})

        else:
            return ({'id': user.id,
                            'email': email,
                            'valid': user.password_matches(password)})

    def __add_account(self, user_id, name, url, info, type, asset_id):
        info = {'name': name, 'url': url, 'info': info, 'type': type,
                'user_id': user_id, 'asset_id': asset_id}
        account = self.__add(Account(**info))
        info['id'] = account.id
        return info

    def __list_accounts(self, user_id):
        found = self.__session.query(Account).filter_by(user_id
                                                        =user_id).all()
        return [{'name': a.name, 'url': a.url, 'info': a.info,
                         'type': a.type, 'user_id': a.user_id,
                         'asset_id': a.asset_id, 'id': a.id}
                        for a in found]

    def __add_statement(self, account_id, start, end,
                      fees, interest, deposits, withdrawals,
                      start_balance, end_balance):
        info = {'account_id': account_id,
                'start': start,  'end': end,
                'fees': fees,  'interest': interest,
                'deposits': deposits,  'withdrawals': withdrawals,
                'start_balance': start_balance,  'end_balance': end_balance}
        statement = self.__add(Statement(**info))
        info['id'] = statement.id
        return info

    def __list_statements(self, account_id):
        found = self.__session.query(Statement).filter_by(account_id
                                                        =account_id).all()
        return [{'account_id': s.account_id,
                         'start': s.start, 'end': s.end,
                         'fees': s.fees, 'interest': s.interest,
                         'deposits': s.deposits,
                         'withdrawals': s.withdrawals,
                         'start_balance': s.start_balance,
                         'end_balance': s.end_balance,
                         'id': s.id}
                        for s in found]

    def run(self):
        engine = self.__init()

        while self.__running:
            command = self.__q.get()

            if None == command:
                break

            # TODO: move to methods and put try/except around them
            try:
                calls = {'user': {
                            'add': self.__add_user,
                            'login': self.__login_user},
                         'account': {
                            'add': self.__add_account,
                            'list': self.__list_accounts},
                         'statement': {
                            'add': self.__add_statement,
                            'list': self.__list_statements}}
                call = calls.get(command[0], {}).get(command[1], None)

                if call:
                    command[2].put(call(*command[3:]))

                else:
                    logging.error('Unable to parse command: ' + str(command))

            except:
                logging.error(traceback.format_exc())
                command[2].put((traceback.format_exc(),))

        self.__session.close()


