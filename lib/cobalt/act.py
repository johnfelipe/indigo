import re
from datetime import date

from lxml import objectify 
from lxml import etree
from lxml.html import _collect_string_content
import arrow

from .uri import FrbrUri

encoding_re = re.compile('encoding="[\w-]+"')

DATE_FORMAT = "%Y-%m-%d"

def datestring(value):
    if value is None:
        return ""
    elif isinstance(value, basestring):
        return value
    else:
        return value.strftime(DATE_FORMAT)


class Act(object):
    """
    An act is a lightweight wrapper around an `Akoma Ntoso 2.0 XML <http://www.akomantoso.org/>`_ act document.
    It provides methods to help access and manipulate the underlying XML directly, in particular
    the metadata for the document.

    The Act object provides quick access to certain sections of the document:

    :ivar root: :class:`lxml.objectify.ObjectifiedElement` root of the XML document
    :ivar meta: :class:`lxml.objectify.ObjectifiedElement` meta element
    :ivar body: :class:`lxml.objectify.ObjectifiedElement` body element

    .. seealso::
        http://www.akomantoso.org/docs/akoma-ntoso-user-documentation/metadata-describes-the-content
    """

    def __init__(self, xml=None):
        """ Setup a new instance with the string in `xml`. """
        if not xml:
            # use an empty document
            xml = EMPTY_DOCUMENT

        encoding = encoding_re.search(xml, 0, 200)
        if encoding:
            # lxml doesn't like unicode strings with an encoding element, so
            # change to bytes
            xml = xml.encode('utf-8')

        self.root = objectify.fromstring(xml)
        self.meta = self.root.act.meta
        self.body = self.root.act.body

        self.namespace = self.root.nsmap[None]
        self._maker = objectify.ElementMaker(annotate=False, namespace=self.namespace, nsmap=self.root.nsmap)


    @property
    def title(self):
        """ Short title """
        return self.meta.identification.FRBRWork.FRBRalias.get('value')

    @title.setter
    def title(self, value):
        self.meta.identification.FRBRWork.FRBRalias.set('value', value)

    @property
    def work_date(self):
        """ Date from the FRBRWork element """
        return arrow.get(self.meta.identification.FRBRWork.FRBRdate.get('date')).date()

    @work_date.setter
    def work_date(self, value):
        self.meta.identification.FRBRWork.FRBRdate.set('date', datestring(value))


    @property
    def expression_date(self):
        """ Date from the FRBRExpression element """
        return arrow.get(self.meta.identification.FRBRExpression.FRBRdate.get('date')).date()

    @expression_date.setter
    def expression_date(self, value):
        self.meta.identification.FRBRExpression.FRBRdate.set('date', datestring(value))


    @property
    def manifestation_date(self):
        """ Date from the FRBRManifestation element """
        return arrow.get(self.meta.identification.FRBRManifestation.FRBRdate.get('date')).date()

    @manifestation_date.setter
    def manifestation_date(self, value):
        self.meta.identification.FRBRManifestation.FRBRdate.set('date', datestring(value))


    @property
    def publication_name(self):
        """ Name of the publication in which this act was published """
        pub = self._get('meta.publication')
        return pub.get('name') if pub is not None else None

    @publication_name.setter
    def publication_name(self, value):
        pub = self._ensure('meta.publication', after=self.meta.identification)
        pub.set('name', value)
        pub.set('showAs', value)


    @property
    def publication_date(self):
        """ Date of the publication """
        pub = self._get('meta.publication')
        return arrow.get(pub.get('date')).date() if pub is not None else None

    @publication_date.setter
    def publication_date(self, value):
        self._ensure('meta.publication', after=self.meta.identification)\
                .set('date', datestring(value))


    @property
    def publication_number(self):
        """ Sequence number of the publication """
        pub = self._get('meta.publication')
        return pub.get('number') if pub is not None else None

    @publication_number.setter
    def publication_number(self, value):
        self._ensure('meta.publication', after=self.meta.identification)\
                .set('number', value)


    @property
    def language(self):
        """ The 3-letter ISO-639-2 language code of this document """
        return self.meta.identification.FRBRExpression.FRBRlanguage.get('language', 'eng')

    @language.setter
    def language(self, value):
        self.meta.identification.FRBRExpression.FRBRlanguage.set('language', value)
        # update the URI
        self.frbr_uri = self.frbr_uri

    @property
    def frbr_uri(self):
        """ The FRBR Work URI as a :class:`FrbrUri` instance that uniquely identifies this document universally. """
        uri = self.meta.identification.FRBRWork.FRBRuri.get('value')
        if uri:
            return FrbrUri.parse(uri)
        else:
            return FrbrUri.empty()

    @frbr_uri.setter
    def frbr_uri(self, value):
        if not isinstance(value, FrbrUri):
            value = FrbrUri.parse(value)

        self.meta.identification.FRBRWork.FRBRuri.set('value', value.work_uri())

        if value.expression_date is None:
            value.expression_date = ''

        value.language = self.meta.identification.FRBRExpression.FRBRlanguage.get('language', 'eng')
        self.meta.identification.FRBRExpression.FRBRuri.set('value', value.expression_uri())
        self.meta.identification.FRBRManifestation.FRBRuri.set('value', value.expression_uri())


    @property
    def year(self):
        """ The act year, derived from :data:`frbr_uri`. Read-only. """
        return self.frbr_uri.date.split("-", 1)[0]

    @property
    def number(self):
        """ The act number, derived from :data:`frbr_uri`. Read-only. """
        return self.frbr_uri.number

    @property
    def nature(self):
        """ The nature of the document, such as an act, derived from :data:`frbr_uri`. Read-only. """
        return self.frbr_uri.doctype

    def to_xml(self):
        return etree.tostring(self.root, pretty_print=True)

    @property
    def body_xml(self):
        """ The raw XML string of the `body` element of the document. When
        setting this property, XML must be rooted at a `body` element. """
        return etree.tostring(self.body, pretty_print=True)

    @body_xml.setter
    def body_xml(self, xml):
        new_body = objectify.fromstring(xml or EMPTY_BODY)
        new_body.tag = 'body'
        self.body.getparent().replace(self.body, new_body)
        self.body = new_body

    def table_of_contents(self):
        """ Get the table of contents of this document as a list of :class:`TOCElement` instances. """

        child_types = [
            '{%s}%s' % (self.namespace, n)
            for n in ['part', 'chapter', 'section']]

        def children(node):
            return node.iterchildren(*child_types)

        def generate_toc(node):
            elem = TOCElement(node)
            elem.children = [generate_toc(c) for c in children(node)]
            return elem

        return [generate_toc(c) for c in children(self.body)]

    def _ensure(self, name, after):
        """ Hack help to get an element if it exists, or create it if it doesn't.
        *name* is a dotted path from *self*, *after* is where to place the new
        element if it doesn't exist. """
        node = self._get(name)
        if node is None:
            # TODO: what if nodes in the path don't exist?
            node = self._make(name.split('.')[-1])
            after.addnext(node)

        return node

    def _make(self, elem):
        return getattr(self._maker, elem)()


    def _get(self, name, root=None):
        parts = name.split('.')
        node = root or self

        for p in parts:
            try:
                node = getattr(node, p)
            except AttributeError:
                return None
        return node

class TOCElement(object):
    """
    An element in the table of contents of a document, such as a chapter, part or section.

    :ivar element: :class:`lxml.objectify.ObjectifiedElement` the XML element of this TOC element
    :ivar type: node type, one of: ``chapter, part, section``
    :ivar id: XML id string of the node in the document, may be None
    :ivar heading: heading for this element, excluding the number, may be None
    :ivar num: number of this element, as a string, may be None
    :ivar children: further TOC elements contained in this one, may be None or empty
    """

    def __init__(self, node, children=None):
        try:
            heading = node.heading
        except AttributeError:
            heading = None

        try:
            num = node.num
        except AttributeError:
            num = None

        self.element = node
        self.type = node.tag.split('}', 1)[-1]
        self.id = node.get('id')
        self.heading = _collect_string_content(heading) if heading else None
        self.num = num.text if num else None
        self.children = children

    def as_dict(self):
      info = {
          'type': self.type,
      }
      if self.heading:
        info['heading'] = self.heading

      if self.num:
        info['num'] = self.num

      if self.id:
        info['id'] = self.id

      if self.children:
        info['children'] = [c.as_dict() for c in self.children]

      return info


EMPTY_DOCUMENT = """<?xml version="1.0"?>
<akomaNtoso xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.akomantoso.org/2.0" xsi:schemaLocation="http://www.akomantoso.org/2.0 akomantoso20.xsd">
  <act contains="originalVersion">
    <meta>
      <identification source="">
        <FRBRWork>
          <FRBRthis value="/za/act/1900/1/main"/>
          <FRBRuri value="/za/act/1900/1"/>
          <FRBRalias value="Untitled"/>
          <FRBRdate date="1900-01-01" name="Generation"/>
          <FRBRauthor href="#council" as="#author"/>
          <FRBRcountry value="za"/>
        </FRBRWork>
        <FRBRExpression>
          <FRBRthis value="/za/act/1900/1/eng@/main"/>
          <FRBRuri value="/za/act/1900/1/eng@"/>
          <FRBRdate date="1900-01-01" name="Generation"/>
          <FRBRauthor href="#council" as="#author"/>
          <FRBRlanguage language="eng"/>
        </FRBRExpression>
        <FRBRManifestation>
          <FRBRthis value="/za/act/1900/1/eng@/main"/>
          <FRBRuri value="/za/act/1900/1/eng@"/>
          <FRBRdate date="1900-01-01" name="Generation"/>
          <FRBRauthor href="#council" as="#author"/>
        </FRBRManifestation>
      </identification>
    </meta>
    <body>
      <section id="section-1">
        <content>
          <p></p>
        </content>
      </section>
    </body>
  </act>
</akomaNtoso>
"""

EMPTY_BODY = """
<body>
  <section id="section-1">
    <content>
      <p></p>
    </content>
  </section>
</body>
"""
