from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from twisted.web.resource import Resource
from flask.ext.classy import FlaskView

import os

class ScrapydWeb():

    def __init__(self, config):
        self.config = config.get("flask_config", "")
        flask = Flask(__name__)
        flask.config.from_pyfile(
            os.path.join(
                flask.root_path,
                self.config
            )
        )
        self.template_path = flask.config["TEMPLATE_DIR"]
        Bootstrap(flask)
        self.flask = flask

    def __call__(self, *args, **kwargs):
        return self.flask.app