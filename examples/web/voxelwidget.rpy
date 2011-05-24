import os

from twisted.web.template import renderer, Element, XMLFile

from bl.ue.web.resource import HTML5TemplatedResource

_here = os.path.dirname(os.path.join(__file__))

class PageElement(Element):
    loader = XMLFile(os.path.join(_here, 'voxelwidget.xhtml'))

resource = HTML5TemplatedResource(PageElement)



