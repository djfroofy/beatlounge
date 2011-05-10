import os

from zope.interface.verify import verifyClass, verifyObject

from twisted.trial.unittest import TestCase
from twisted.python import log
from twisted.web.template import Element, renderer, XMLFile

from bl.ue.web.resource import IDeferredResource, HTML5Resource
from bl.ue.web.resource import HTML5TemplatedResource

_here = os.path.dirname(__file__)

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


class TestElement(Element):
    loader = XMLFile(os.path.join(_here, 'test.xhtml'))

    @renderer
    def header(self, request, tag):
        return tag('Header. request.method=%s' % request.method)

    @renderer
    def footer(self, request, tag):
        return tag('Footer.')


class HTML5TemplatedResourceTests(TestCase):

    def test_template_rendering(self):
        r = HTML5TemplatedResource(TestElement)
        req = DummyRequest()
        r.render(req)

        expected = '''<!doctype html>

<html>
<body>
  <div>Header. request.method=GET</div>
  <div id="content">
    <p>Content goes here.</p>
  </div>
  <div>Footer.</div>
</body>
</html>'''
        rendered = '\n'.join(req.written)
        self.assertEquals(rendered, expected)


