#!/usr/bin/env python3


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
        return value / 100.0


class InterestRate(sqlalchemy.types.TypeDecorator):
    impl = sqlalchemy.Integer

    def process_bind_param(self, value, dialect):
        return int(value * 1000.0 + 0.005)

    def process_result_value(self, value, dialect):
        return value / 1000.0


class Date(sqlalchemy.types.TypeDecorator):
    impl = sqlalchemy.types.Date

    def process_bind_param(self, value, dialect):
        if None == value:
            return value

        try:  # if it is a string, parse it, otherwise it must be datetime object
            return datetime.datetime.strptime(value, "%Y/%m/%d")
        except TypeError:
            return value

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

    def get_info(self):
        return {'id': self.id, 'email': self.email, 'password_hash': self.password_hash}

    def __repr__(self):
        return 'User(id=%s, email="%s", password_hash="%s")'%(self.id,
                                                              self.email,
                                                              self.password_hash)


class Feedback(Alchemy_Base):
    __tablename__ = 'feedback'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('user.id'))
    user = sqlalchemy.orm.relationship('User', backref='feedback')
    type = sqlalchemy.Column(sqlalchemy.String(32))
    subject = sqlalchemy.Column(sqlalchemy.String(1024))
    description = sqlalchemy.Column(sqlalchemy.String(4096))

    def get_info(self):
        return {'id': self.id, 'user_id': self.user_id, 'type': self.type,
                'subject': self.subject, 'description': self.description}

    def __repr__(self):
        return ('Feedback(id=%s, '
                + 'user_id=%d '
                + 'type="%s", '
                + 'subject="%s", '
                + 'description="%s")')%(self.id,
                                        self.user_id,
                                        self.type,
                                        self.subject,
                                        self.description)


class Feedback_Relationship(Alchemy_Base):
    __tablename__ = 'feedback_relationship'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    from_type = sqlalchemy.Column(sqlalchemy.String(32))
    to_type = sqlalchemy.Column(sqlalchemy.String(32))
    from_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey('feedback.id'))
    to_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey('feedback.id'))

    def get_info(self):
        return {'id': self.id, 'from_type': self.from_type, 'to_type': self.to_type,
                'from_id': self.from_id, 'to_id': self.to_id}

    def __repr__(self):
        return ('Feedback_Relationship(id=%s, ' +
                'from_type="%s", ' +
                'to_type="%s", ' +
                'from_id=%d, ' +
                'to_id=%d)')%(self.id, self.from_type, self.to_type,
                              self.from_id, self.to_id)


class Feedback_Votes(Alchemy_Base):
    __tablename__ = 'feedback_votes'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('user.id'))
    user = sqlalchemy.orm.relationship('User', backref='votes')
    feedback_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('feedback.id'))
    feedback = sqlalchemy.orm.relationship('Feedback', backref='votes')
    votes = sqlalchemy.Column(sqlalchemy.Integer)

    def get_info(self):
        return {'id': self.id, 'user_id': self.user_id, 'feedback_id': self.feedback_id,
                'votes': self.votes}

    def __repr__(self):
        return ('Feedback_Votes(id=%s, ' +
                'user_id=%d, ' +
                'feedback_id=%d, ' +
                'votes=%d)')%(self.id, self.user_id, self.feedback_id,self.votes)


class Account(Alchemy_Base):
    __tablename__ = 'account'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String(100))
    url = sqlalchemy.Column(sqlalchemy.String(1024))
    info = sqlalchemy.Column(sqlalchemy.String(4096))
    interest_rate = sqlalchemy.Column(InterestRate())
    type = sqlalchemy.Column(sqlalchemy.String(5))
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('user.id'))
    user = sqlalchemy.orm.relationship('User', backref='accounts')
    asset_id = sqlalchemy.Column(sqlalchemy.Integer,
                                 sqlalchemy.ForeignKey('account.id'))
    asset = sqlalchemy.orm.relationship('Account')
    debts = sqlalchemy.orm.relationship('Account', remote_side=[id])

    def get_info(self):
        return {'id': self.id, 'name': self.name, 'url': self.url,
                'info': self.info, 'interest_rate': self.interest_rate,
                'type': self.type, 'user_id': self.user_id, 'asset_id': self.asset_id}

    def __repr__(self):
        return ('Account(id=%s, name="%s", ' +
               'type="%s", interest rate=%0.3f%% url="%s", info="%s", ' +
               ' user_id=%s, asset_id=%s)')%(self.id, self.name, self.type,
                                             self.interest_rate,
                                             self.url, self.info, self.user_id,
                                             self.asset_id)


class Statement(Alchemy_Base):
    __tablename__ = 'statement'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    start = sqlalchemy.Column(Date)
    due = sqlalchemy.Column(Date)
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

    def get_info(self):
        return {'id': self.id, 'start': self.start, 'due': self.due,
                'end': self.end, 'fees': self.fees,
                'interest': self.interest, 'deposits': self.deposits,
                'withrawals': self.withrawals,
                'start_balance': self.start_balance, 'end_balance': self.end_balance,
                'account_id': self.account_id}

    def __repr__(self):
        return ('Statement(id=%s, start="%s", end="%s", ' +
                'due="%s", ' +
                'fees=$%0.2f, interest=$%0.2f, ' +
                'deposits=$%0.2f, withdrawals=$%0.2f, ' +
                'start_balance=$%0.2f, end_balance=$%0.2f, ' +
                'account_id=%s)')%(self.id, self.start, self.end, self.due,
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

    def add_user(self, email, password):
        results = queue.Queue()
        self.__q.put((self.__add_user, results, email, password))
        return results.get()

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

    def login_user(self, email, password):
        results = queue.Queue()
        self.__q.put((self.__login_user, results, email, password))
        return results.get()

    def __add_account(self, user_id, name, url, info, type, interest_rate, asset_id):
        info = {'name': name, 'url': url, 'info': info, 'type': type,
                'user_id': user_id, 'interest_rate': interest_rate,
                'asset_id': asset_id}
        account = self.__add(Account(**info))
        info['id'] = account.id
        return info

    def add_account(self, user_id, name, url, info, type, interest_rate=0.0,
                    asset_id=None):
        results = queue.Queue()
        self.__q.put((self.__add_account, results, user_id, name, url, info,
                      type, interest_rate, asset_id))
        return results.get()

    def __list_accounts(self, user_id):
        found = self.__session.query(Account).filter_by(user_id
                                                        =user_id).all()
        return [{'name': a.name, 'url': a.url, 'info': a.info,
                         'type': a.type, 'user_id': a.user_id,
                         'interest_rate': a.interest_rate,
                         'asset_id': a.asset_id, 'id': a.id}
                        for a in found]

    def list_accounts(self, user_id):
        results = queue.Queue()
        self.__q.put((self.__list_accounts, results, user_id))
        return results.get()

    def __add_statement(self, account_id, start, end, due,
                      fees, interest, deposits, withdrawals,
                      start_balance, end_balance):
        info = {'account_id': account_id,
                'start': start,  'end': end, 'due': due,
                'fees': fees,  'interest': interest,
                'deposits': deposits,  'withdrawals': withdrawals,
                'start_balance': start_balance,  'end_balance': end_balance}
        statement = self.__add(Statement(**info))
        info['id'] = statement.id
        return info

    def add_statement(self, account_id, start, end, due,
                      fees, interest, deposits, withdrawals,
                      start_balance, end_balance):
        results = queue.Queue()
        self.__q.put((self.__add_statement, results, account_id,  start, end, due,
                      fees, interest, deposits, withdrawals,
                      start_balance, end_balance))
        return results.get()

    def __list_statements(self, account_id):
        found = self.__session.query(Statement).filter_by(account_id
                                                        =account_id).all()
        return [{'account_id': s.account_id,
                         'start': s.start, 'end': s.end, 'due': s.due,
                         'fees': s.fees, 'interest': s.interest,
                         'deposits': s.deposits,
                         'withdrawals': s.withdrawals,
                         'start_balance': s.start_balance,
                         'end_balance': s.end_balance,
                         'id': s.id}
                        for s in found]

    def list_statements(self, account_id):
        results = queue.Queue()
        self.__q.put((self.__list_statements, results, account_id))
        return results.get()

    def __add_feedback(self, user_id, type, subject, description):
        info = {'user_id': user_id, 'type': type, 'subject': subject, 'description': description}
        statement = self.__add(Feedback(**info))
        info['id'] = statement.id
        return info

    def add_feedback(self, user_id, type, subject, description):
        results = queue.Queue()
        self.__q.put((self.__add_feedback, results, user_id, type, subject, description))
        return results.get()

    def __list_feedback(self, user_id):
        found = self.__session.query(Feedback).filter_by(user_id
                                                        =user_id).all()
        return [{'user_id': s.user_id,
                 'type': s.type, 'subject': s.subject, 'description': s.description,
                 'id': s.id}
                for s in found]

    def list_feedback(self, user_id):
        results = queue.Queue()
        self.__q.put((self.__list_feedback, results, user_id))
        return results.get()

    def __relate_feedback(self, from_id, to_id, from_type, to_type):
        info = {'from_id': from_id, 'to_id': to_id,
                'from_type': from_type, 'to_type': to_type}
        statement = self.__add(Feedback_Relationship(**info))
        info['id'] = statement.id
        return info

    def relate_feedback(self, from_id, to_id, from_type, to_type):
        results = queue.Queue()
        self.__q.put((self.__relate_feedback, results, from_id, to_id,
                      from_type, to_type))
        return results.get()

    def __list_related_feedback(self, feedback_id):
        query = self.__session.query(Feedback_Relationship)
        found = query.filter(sqlalchemy.or_(Feedback_Relationship.from_id
                                               ==feedback_id,
                                               Feedback_Relationship.to_id
                                               ==feedback_id)).all()
        feedback_query = self.__session.query(Feedback)
        return [{'from_id': s.from_id, 'to_id': s.to_id,
                 'from_type': s.from_type, 'to_type': s.to_type,
                 'from': feedback_query.get(s.from_id).get_info(),
                 'to': feedback_query.get(s.to_id).get_info()}
                for s in found]

    def list_related_feedback(self, feedback_id):
        results = queue.Queue()
        self.__q.put((self.__list_related_feedback, results, feedback_id))
        return results.get()

    def __feedback_vote(self, user_id, feedback_id, votes=None):
        query = self.__session.query(Feedback_Votes)
        found = query.filter_by(feedback_id=feedback_id,
                                user_id=user_id).one_or_none()

        if not found:
            found = Feedback_Votes(user_id=user_id,
                                   feedback_id=feedback_id,
                                   votes=votes if votes else 0)

        elif votes:
            found.votes = votes

        return found

    def feedback_vote(self, user_id, feedback_id, votes=None):
        results = queue.Queue()
        self.__q.put((self.__feedback_vote, results, user_id, feedback_id, votes))
        return results.get()

    def __feedback_all_votes(self, feedback_id):
        query = self.__session.query(Feedback_Votes)
        found = query.filter_by(feedback_id=feedback_id).all()
        return [v.get_info() for v in found]

    def feedback_all_votes(self, feedback_id):
        results = queue.Queue()
        self.__q.put((self.__feedback_all_votes, results, feedback_id))
        return results.get()

    def run(self):
        engine = self.__init()

        while self.__running:
            command = self.__q.get()

            if None == command:
                break

            try:
                command[1].put(command[0](*command[2:]))

            except:
                logging.error(traceback.format_exc())
                command[1].put((traceback.format_exc(),))

        self.__session.close()


