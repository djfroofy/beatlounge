from zope.interface import implements

from twisted.python import log
from twisted.internet.defer import maybeDeferred

from twisted.web.resource import IResource, Resource
from twisted.web.server import NOT_DONE_YET
from twisted.web.template import flattenString

try:
    from lxml.hmtl import html5parser
except ImportError:
    html5parser = None


class IDeferredResource(IResource):
    """
    A Custom IResource that can return a Deferred from
    render_GET instead of NOT_DONE_YET.
    """

    def render_GET(request):
        """
        Return response as string or a Deferred which will fire when finished
        writing to the request. Providers should not call request.finish() as
        this is done in a finalizing callback attached in render().
        """

class HTML5Resource(Resource):
    """
    A resource for HTML5 content.
    """
    implements(IDeferredResource)
    validate = False
    html5Newline = '\n'

    def render(self, request):
        request.write('<!doctype html>%s' % self.html5Newline)
        d = maybeDeferred(Resource.render, self, request)
        d.addCallback(self._finalizeResponse, request)
        return NOT_DONE_YET

    def render_GET(self, request):
        """
        Sublasses should override and return either a string, None or a
        Deferred. Nowhere should the implementation call request.finish() as
        this is done after render().
        """

    def _finalizeResponse(self, data, request):
        """
        Finalize the response calling request.finish. If validate on
        this resource is True and lxml.html.html5parser is available we'll try
        parse the rendered page and gripe if we can't.
        """
        if data:
            request.write(data)
        if self.validate:
            # TODO validate the content
            pass
        request.finish()


class HTML5TemplatedResource(HTML5Resource):
    """
    An HTML5 templated by twisted.web.template.Element. Just supply
    an Element subclass to the constructor and we'll take care
    of the redering in render_GET for you.
    """


    def __init__(self, elementClass):
        Resource.__init__(self)
        self.elementClass = elementClass

    def render_GET(self, request):
        """
        Return a Deferred that will fire after we have flattened
        our Element into a string.
        """
        element = self.elementClass()
        return flattenString(request, element)

class TemplatedResourceMixin(object):

    elementClass = None

    def renderTemplate(self, request):
        element = self.elementClass()
        return flattenString(request, element)


class HTML5TemplatedResource(HTML5Resource, TemplatedResourceMixin):
    """
    An HTML5 templated by twisted.web.template.Element. Just supply
    an Element subclass to the constructor and we'll take care
    of the redering in render_GET for you.
    """


    def __init__(self, elementClass):
        Resource.__init__(self)
        self.elementClass = elementClass

    def render_GET(self, request):
        """
        Return a Deferred that will fire after we have flattened
        our Element into a string.
        """
        return self.renderTemplate(request)




