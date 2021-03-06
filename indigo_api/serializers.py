import logging

from lxml.etree import LxmlError

from rest_framework import serializers, renderers
from rest_framework.reverse import reverse
from rest_framework.exceptions import ValidationError
from cobalt import Act, FrbrUri

from .models import Document
from .importer import Importer

log = logging.getLogger(__name__)

class DocumentSerializer(serializers.HyperlinkedModelSerializer):
    body = serializers.CharField(required=False, write_only=True)
    """ A write-only field for setting the body of the document. """

    body_url = serializers.SerializerMethodField()
    """ A read-only URL for the body of the document. The body isn't included in the
    document description because it could be huge. """

    content = serializers.CharField(required=False, write_only=True)
    """ A write-only field for setting the entire XML content of the document. """

    content_url = serializers.SerializerMethodField()
    """ A URL for the entire content of the document. The content isn't included in the
    document description because it could be huge. """

    toc_url = serializers.SerializerMethodField()
    """ A URL for the table of content of the document. The TOC isn't included in the
    document description because it could be huge and requires parsing the XML. """

    published_url = serializers.SerializerMethodField()
    """ Public URL of a published document. """

    file = serializers.FileField(write_only=True, required=False)
    """ Allow uploading a file to convert and override the content of the document. """

    class Meta:
        model = Document
        fields = (
                # readonly, url is part of the rest framework
                'id', 'url',

                'content', 'content_url', 'file',
                'body', 'body_url',

                'frbr_uri', 'draft', 'created_at', 'updated_at',
                'title', 'country', 'number', 'year', 'nature',
                'publication_date', 'publication_name', 'publication_number',
                'language',

                'published_url', 'toc_url',
                )
        read_only_fields = ('number', 'nature', 'created_at', 'updated_at', 'year')

    def get_body_url(self, doc):
        if not doc.pk:
            return None
        return reverse('document-body', request=self.context['request'], kwargs={'pk': doc.pk})

    def get_content_url(self, doc):
        if not doc.pk:
            return None
        return reverse('document-content', request=self.context['request'], kwargs={'pk': doc.pk})

    def get_toc_url(self, doc):
        if not doc.pk:
            return None
        return reverse('document-toc', request=self.context['request'], kwargs={'pk': doc.pk})

    def get_published_url(self, doc):
        if not doc.pk or doc.draft:
            return None
        else:
            uri = doc.doc.frbr_uri
            uri.expression_date = None
            uri = uri.expression_uri()[1:]

            return reverse('published-document-detail', request=self.context['request'],
                    kwargs={'frbr_uri': uri})

    def validate(self, data):
        """
        We allow callers to pass in a file upload in the ``file`` attribute,
        and overwrite the content XML with that value if we can.
        """
        upload = data.pop('file', None)
        if upload:
            # we got a file
            try:
                document = Importer().import_from_upload(upload)
            except ValueError as e:
                log.error("Error during import: %s" % e.message, exc_info=e)
                raise ValidationError({'file': e.message or "error during import"})
            data['content'] = document.content

        return data

    def validate_content(self, value):
        try:
            Act(value)
        except LxmlError as e:
            raise ValidationError("Invalid XML: %s" % e.message)
        return value

    def validate_frbr_uri(self, value):
        try:
            return FrbrUri.parse(value).work_uri()
        except ValueError as e:
            raise ValidationError("Invalid FRBR URI")

    def update_document(self, instance):
        """ Update document without saving it. """
        for attr, value in self.validated_data.items():
            setattr(instance, attr, value)
        return instance


class ConvertSerializer(serializers.Serializer):
    """
    Helper to handle input elements for the /convert API
    """

    file = serializers.FileField(write_only=True, required=False)
    content = serializers.CharField(write_only=True, required=False)
    inputformat = serializers.ChoiceField(write_only=True, required=False, choices=['json'])
    outputformat = serializers.ChoiceField(write_only=True, required=True, choices=['xml', 'json', 'html'])

    def validate(self, data):
        if data.get('content') and not data.get('inputformat'):
            raise ValidationError({'inputformat': "The inputformat field is required when the content field is used"})

        return data


class AkomaNtosoRenderer(renderers.XMLRenderer):
    def render(self, data, media_type=None, renderer_context=None):
        return data
