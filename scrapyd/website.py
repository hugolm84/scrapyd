from twisted.web import resource
from twisted.application.service import IServiceCollection

from scrapy.utils.misc import load_object

from .interfaces import IPoller, IEggStorage, ISpiderScheduler

from twisted.web.wsgi import WSGIResource
from twisted.internet import reactor


class Root(resource.Resource):

    def __init__(self, config, app):
        resource.Resource.__init__(self)
        self.debug = config.getboolean('debug', False)
        self.runner = config.get('runner')
        self.items_dir = config.get("items_dir")
        self.logs_dir = config.get("logs_dir")

        self.config = config
        self.app = app

        web_path = config.get("web_app")

        if web_path:
            web_app = load_object(web_path)
            webcls = web_app(self)
            self.wsgi = WSGIResource(reactor, reactor.getThreadPool(), webcls.create())

        services = config.items('services', ())
        for servName, servClsName in services:
            servCls = load_object(servClsName)
            self.putChild(servName, servCls(self))

        self.update_projects()

    def getChild(self, path, request):
        if self.wsgi:
            request.prepath.pop()
            request.postpath.insert(0, path)
            return self.wsgi
        return self

    def update_projects(self):
        self.poller.update_projects()
        self.scheduler.update_projects()

    @property
    def launcher(self):
        app = IServiceCollection(self.app, self.app)
        return app.getServiceNamed('launcher')

    @property
    def scheduler(self):
        return self.app.getComponent(ISpiderScheduler)

    @property
    def eggstorage(self):
        return self.app.getComponent(IEggStorage)

    @property
    def poller(self):
        return self.app.getComponent(IPoller)