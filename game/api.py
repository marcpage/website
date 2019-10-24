import argparse
import os
import time
import threading
import traceback

from flask import Flask, request, redirect, jsonify

#import credentials
credentials = type('creds', (), {})(); credentials.url = 'sqlite:////tmp/db.test.sqlite3'
import db

DB = None


def create_app(source_dir, template_dir):
    app = Flask(__name__, static_folder=source_dir,
                template_folder=template_dir)

    @app.route("/")
    def index():  # pylint: disable=unused-variable
        """Return page on root path"""
        return (jsonify({'yep': 200}), 200)

    @app.route("/api/login", methods=['POST'])
    def login():  # pylint: disable=unused-variable

        try:
            request_form = request.get_json()
            user = DB.login_user(request_form['email'], request_form['password'])
        except:
            return (jsonify({'error': traceback.format_exc(), 'type': 'exception'}), 400)

        if not user.id and not user.password_hash:
            return (jsonify({'error': 'Email does not exists: ' + request_form['email'],
                             'field': 'email'}), 400)

        if not user.id:
            return (jsonify({'error': 'Bad password', 'field': 'password'}), 400)

        return (jsonify({'email': user.email,
                         'id': user.id,
                         'password_hash': user.password_hash}), 200)

    @app.route("/api/login/create", methods=['POST'])
    def create_login():  # pylint: disable=unused-variable

        try:
            request_form = request.get_json()
            user = DB.add_user(request_form['email'], request_form['password'])
        except:
            return (jsonify({'error': traceback.format_exc(), 'type': 'exception'}), 400)

        if not user.password_hash:
            return (jsonify({'error': 'Email already exists: ' + request_form['email'],
                             'field': 'email', 'reason': 'duplicate'}), 400)

        return (jsonify({'email': user.email,
                         'id': user.id,
                         'password_hash': user.password_hash}), 200)

    @app.errorhandler(404)
    def page_not_found(error):  # pylint: disable=unused-argument,unused-variable
        """ If they access a page that is not available, show the error message.
            error - the error of type werkzeug.exceptions.NotFound
        """
        return (jsonify({'error': 'Bad URL: ' + request.url}), 404)

    return app

def parse_args():
    """ Parses and returns command line arguments.
    """

    parser = argparse.ArgumentParser(description='Serves the api for the game.')
    parser.add_argument('-p', '--port', type=int, default=80,
                        help='The port to listen on (default 80)')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Debug the web server')
    parser.add_argument('-u', '--ui', type=str, default='/tmp',
                        help='Path to the UI directory.')
    args = parser.parse_args()

    return args


def main():
    args = parse_args()
    with db.Connect(credentials.url) as database:
        global DB
        DB = database
        app = create_app(args.ui, os.path.join(args.ui, 'template'))
        app.run(host='0.0.0.0', debug=args.debug, port=args.port)


if __name__ == '__main__':
    main()
