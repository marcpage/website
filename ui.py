#!/usr/bin/env python3

import tornado.web
import argparse
import logging
import mako.template
import db


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        template = mako.template.Template(filename='ui/index.html.mako')
        self.write(template.render(title='Welcome to Relifi Game', logged_in=False))


class LoginHandler(tornado.web.RequestHandler):
    def get(self):
        template = mako.template.Template(filename='ui/redirect.html.mako')
        self.write(template.render(title='Redirect to /', redirect='/'))


def parse_args():
	parser = argparse.ArgumentParser(description='Financial Game')
	parser.add_argument('-p', '--port', default='8000',
	                    help='Port to listen on for http connections')
	args = parser.parse_args()
	return args


def main(args):
    logging.basicConfig(filename='/tmp/game_log.txt',level=logging.INFO)
    server = tornado.web.Application([
        (r"/", MainHandler),
        (r"/login", LoginHandler),
    ])
    server.listen(args.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main(parse_args())
