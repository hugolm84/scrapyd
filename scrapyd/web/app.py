import os
from datetime import datetime
from flask import Flask, render_template
from flask import Blueprint
from flask_bootstrap import Bootstrap
from twisted.web import resource
from scrapyd.utils import get_spider_list, UtilsCache

class FlaskApp(resource.Resource):

    date_format = '%Y-%m-%d-%H:%M:%S.%f'

    def __init__(self, root):
        resource.Resource.__init__(self)
        self.root = root

    def create(self):
        flask = Flask(__name__)
        flask.config.from_pyfile(os.path.join(flask.root_path,self.root.config.get("web_conf")))
        for error in range(400, 420) + range(500,506):
            flask.error_handler_spec[None][error] = self.generic_error_handler

        if flask.config["TEMPLATE_DIR"]:
            flask.template_folder = flask.config["TEMPLATE_DIR"]

        if flask.config["AUTOINDEX_ITEMS"]:
            self.register_auto_index_items(flask)

        if flask.config["AUTOINDEX_LOGS"]:
            self.register_auto_index_logs(flask)

        Bootstrap(flask)

        @flask.route("/")
        def index():
            return render_template("index.html", page_title="Home", jobs = self.get_jobs())

        @flask.route("/spiders")
        def projects():
            project_spiders = []
            scrapyd_error = None
            for project in self.root.scheduler.list_projects():
                if project is '.DS_Store':
                    pass
                try:
                    project_spiders.append({'name': project, 'spiders': get_spider_list(project, runner=self.root.runner)})
                except RuntimeError, e:
                    scrapyd_error = "%s: %s" % (project, e.message)

            return render_template("spiders.html", page_title="Spiders", project_spiders=project_spiders,
                                   error=scrapyd_error)
        return flask

    def generic_error_handler(self, error):
        view = {
            "code": error.code,
            "description": error.description,
            "name": error.name,
            "page_title": "Error %d %s" % (error.code, error.name),
            }

        return render_template("error.html", **view), error.code

    def register_auto_index_items(self, flask):
        from flask.ext.autoindex import AutoIndexBlueprint
        auto_items = Blueprint('auto_items', __name__)
        AutoIndexBlueprint(auto_items, browse_root=self.root.items_dir)
        flask.register_blueprint(auto_items, url_prefix='/items')

    def register_auto_index_logs(self, flask):
        from flask.ext.autoindex import AutoIndexBlueprint
        auto_logs = Blueprint('auto_logs', __name__)
        AutoIndexBlueprint(auto_logs, browse_root=self.root.logs_dir)
        flask.register_blueprint(auto_logs, url_prefix='/logs')


    def queue_item(self, p, m):
        return {'project': p, 'name': str(m['name']), 'job': str(m['_job']),
                'items': '', 'logs': '', 'runtime': ''}

    def launcher_item(self, p, d):
        return {'project': p.project, 'name': p.spider, 'job': p.job,
                'items': '/items/%s/%s/%s/%s.json' % (p.project, p.spider, p.job, p.job),
                'log': '/logs/%s/%s/%s/%s.log' % (p.project, p.spider, p.job, p.job),
                'runtime': (d - p.start_time),
                'date' : p.start_time.strftime(self.date_format)}

    def get_jobs(self):

        jobs = {'queued': [], 'running': [], 'finished': []}

        for project, queue in self.root.poller.queues.items():
            for m in queue.list():
                jobs['queued'].append(self.queue_item(project, m))

        for p in self.root.launcher.processes.values():
            jobs['running'].append(self.launcher_item(p, datetime.now()))

        for p in self.root.launcher.finished:
            jobs['finished'].append(self.launcher_item(p, p.end_time))

        return jobs
