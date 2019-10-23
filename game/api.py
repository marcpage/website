import argparse
import os
import time

from flask import Flask, request, redirect, jsonify

import db

def create_app(source_dir, template_dir):
    app = Flask(__name__, static_folder=source_dir,
                template_folder=template_dir)

    @app.route("/")
    def index():  # pylint: disable=unused-variable
        """Return page on root path"""
        return (jsonify({'yep': 200}), 200)

    @app.errorhandler(404)
    def page_not_found(error):  # pylint: disable=unused-argument,unused-variable
        """ If they access a page that is not available, show the error message.
            error - the error of type werkzeug.exceptions.NotFound
        """

        return (jsonify({'error': request.url}), 404)

    return app

def parse_args():
    """ Parses and returns command line arguments.
    """

    parser = argparse.ArgumentParser(description='Serves the api for the game.')
    parser.add_argument('-p', '--port', type=int, default=80,
                        help='The port to listen on (default 80)')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Debug the web server')
    parser.add_argument('-u', '--ui', type=str, required=True,
                        help='Path to the UI directory.')
    args = parser.parse_args()

    return args


def main():
    args = parse_args()
    app = create_app(args.ui, os.path.join(args.ui, 'template'))
    app.run(host='0.0.0.0', debug=args.debug, port=args.port)


if __name__ == '__main__':
    main()
