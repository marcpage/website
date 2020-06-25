#!/usr/bin/env python


__all__ = ['Connect']


import sqlalchemy
import sqlalchemy.ext.declarative
import threading
import queue
import logging
import hashlib


Alchemy_Base = sqlalchemy.ext.declarative.declarative_base()


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
    type = sqlalchemy.Column(sqlalchemy.String(5))
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('user.id'))
    user = sqlalchemy.orm.relationship('User', backref='accounts')
    asset_id = sqlalchemy.Column(sqlalchemy.Integer,
                                 sqlalchemy.ForeignKey('account.id'))
    asset = sqlalchemy.orm.relationship('Account')
    debts = sqlalchemy.orm.relationship('Account', remote_side=[id])


    def __repr__(self):
        return ('Account(id=%s, name="%s", ' +
               'type="%s", bank_id=%s, user_id=%s)')%(self.id, self.name, self.type,
                                                    self.bank_id, self.user_id)


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

    def run(self):
        engine = self.__init()

        while self.__running:
            command = self.__q.get()

            if None == command:
                break

            if command[0] == 'user':

                if command[1] == 'add':
                    user = self.__find_user(email=command[3])

                    if user:
                        command[2].put({'id': None, 'valid': False})

                    else:
                        password_hash = password_hash=User.hash(command[4])
                        user = self.__add(User(email=command[3],
                                               password_hash=password_hash))
                        command[2].put({'id': user.id,
                                        'email': command[3],
                                        'valid': True})

                    continue

                elif command[1] == 'login':
                    user = self.__find_user(email=command[3])

                    if not user:
                        command[2].put({'id': None,
                                        'email': command[3],
                                        'valid': False})

                    else:
                        command[2].put({'id': user.id,
                                        'email': command[3],
                                        'valid': user.password_matches(command[4])})

                    continue


            logging.error('Unable to parse command: ' + str(command))

        self.__session.close()


