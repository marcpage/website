#!/usr/bin/env python3

import tornado.web
import argparse
import logging
import mako.template
import db
import os

class MainHandler(tornado.web.RequestHandler):
    def initialize(self, storage):
        self.__storage = storage

    def get(self, user_id=None):
        template = mako.template.Template(filename='ui/index.html.mako')
        self.write(template.render(title='Welcome to Relifi Game',
                                   logged_in=user_id))


class LoginHandler(tornado.web.RequestHandler):
    def initialize(self, storage):
        self.__storage = storage

    def get(self):
        template = mako.template.Template(filename='ui/redirect.html.mako')
        email = self.get_body_argument('email')
        password = self.get_body_argument('password')
        user = self.__storage.login_user(email, password)

        if not user['id']:
            self.write(template.render(title='Redirect to /', redirect='/#bademail'))

        elif not user['valid']:
            self.write(template.render(title='Redirect to /', redirect='/#badpassword'))

        else:
            self.write(template.render(title='Redirect to /user/' + str(user['id']),
                                       redirect='/user/' + str(user['id'])))

    def post(self):
        self.get()

def parse_args():
	parser = argparse.ArgumentParser(description='Financial Game')
	parser.add_argument('-p', '--port', default='8000',
	                    help='Port to listen on for http connections')
	parser.add_argument('-u', '--url',
	                    default='sqlite:////%s/.game.sqlite3'%(os.environ['HOME']),
	                    help='Port to listen on for http connections')
	args = parser.parse_args()
	return args


def main(args):
    try:
        with db.Connect(args.url) as storage:
            logging.basicConfig(filename='/tmp/game_log.txt',level=logging.INFO)
            server = tornado.web.Application([
                (r"/", MainHandler, dict(storage=storage)),
                (r"/user/(.*)", MainHandler, dict(storage=storage)),
                (r"/login", LoginHandler, dict(storage=storage)),
            ])
            server.listen(args.port)
            tornado.ioloop.IOLoop.current().start()
    except:
        raise
    finally:
        pass


if __name__ == '__main__':
    main(parse_args())

