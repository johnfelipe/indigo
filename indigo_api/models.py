import logging

from django.db import models
from indigo_an.act import Act

COUNTRIES = sorted([
        ('za', 'South Africa'),
        ('zm', 'Zambia'),
        ])

log = logging.getLogger(__name__)

class Document(models.Model):
    db_table = 'documents'

    uri = models.CharField(max_length=512, null=True, unique=True)
    """ The FRBRuri of this document that uniquely identifies it globally """

    title = models.CharField(max_length=1024, null=True)
    country = models.CharField(max_length=2, choices=COUNTRIES, default=COUNTRIES[0][0])
    draft = models.BooleanField(default=True, help_text="Drafts aren't available through the public API")
    """ Is this a draft? """

    document_xml = models.TextField(null=True, blank=True)
    """ Raw XML content of the entire document """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def doc(self):
        """ The wrapped `an.act.Act` that this document works with. """
        if not hasattr(self, '_doc'):
            self._doc = Act(self.document_xml)
        return self._doc

    @property
    def body_xml(self):
        return self.doc.body_xml

    @body_xml.setter
    def body_xml(self, xml):
        log.debug("Set body_xml to: %s" % xml)
        self.doc.body_xml = xml

    def save(self, *args, **kwargs):
        self.copy_attributes()
        return super(Document, self).save(*args, **kwargs)

    def copy_attributes(self):
        """ Override to update the XML document. """
        self.doc.title = self.title
        self.doc.frbr_uri = self.uri

        log.debug("Refreshing document xml")
        self.document_xml = self.doc.to_xml()

    def __unicode__(self):
        return 'Document<%s, %s>' % (self.id, (self.title or '(Untitled)')[0:50])
