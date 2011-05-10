from zope.interface.verify import verifyClass, verifyObject

from twisted.trial.unittest import TestCase
from twisted.python import log

from bl.ue.web.resource import IDeferredResource, HTML5Resource


class TestHTML5Resource(HTML5Resource):

    def render_GET(self, request):
        return '<h1>Hello</h1>'

class TestDeferredHTML5Resource(HTML5Resource):

    d = None

    def render_GET(self, request):
        TestDeferredHTML5Resource.deferred = d = Deferred()
        reactor.callLater(0, d.callback, '<h1>Deferred Hello</h1>')
        return d


class DummyRequest:
    method = 'GET'
    finished = False

    def __init__(self):
        self.written = []

    def write(self, data):
        if self.finished:
            log.err('request is finished')
            return
        self.written.append(data)

    def finish(self):
        if self.finished:
            log.err('finish called twice')
            return
        self.finished = True


class HTML5ResourceTests(TestCase):

    def test_interface(self):
        verifyClass(IDeferredResource, HTML5Resource)
        verifyObject(IDeferredResource, HTML5Resource())


    def test_basic_resource(self):
        resource = TestHTML5Resource()
        req = DummyRequest()
        resource.render(req)
        self.assertEquals(''.join(req.written), '<!doctype html>\n<h1>Hello</h1>')
        self.assert_(req.finished)

    def test_deferred_resource(self):
        resource = TestHTML5Resource()
        req = DummyRequest()
        def check(ignore):
            self.assertEquals(''.join(req.written),
                              '<!doctype html>\n<h1>Deferred Hello</h1>')
            self.assert_(req.finished)
        return resource.render(req)


