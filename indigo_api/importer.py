import subprocess
import tempfile
import shutil
import logging

from django.conf import settings

from .models import Document

class Importer(object):
    """
    Import from PDF and other document types using Slaw.

    Slaw is a commandline tool from the slaw Ruby Gem which generates Akoma Ntoso
    from PDF and other documents. See https://rubygems.org/gems/slaw
    """
    log = logging.getLogger(__name__)

    def import_from_upload(self, upload):
        """ Create a new Document by importing it from a
        :class:`django.core.files.uploadedfile.UploadedFile` instance.
        """
        if upload.content_type in ['text/xml', 'application/xml']:
            doc = Document()
            doc.content = upload.read().decode('utf-8')
        else:
            with self.tempfile_for_upload(upload) as f:
                doc = self.import_from_file(f.name)
            doc.title = "Imported from %s" % upload.name
            doc.copy_attributes()

        return doc

    def import_from_file(self, fname):
        cmd = ['parse', '--no-definitions'] + [fname]
        code, stdout, stderr = self.slaw(cmd)

        if code > 0:
            raise ValueError("Error converting file: %s" % stderr)

        if not stdout:
            raise ValueError("We couldn't get any useful text out of the file")

        doc = Document()
        doc.content = stdout.decode('utf-8')

        self.log.info("Successfully imported from %s" % fname)
        return doc

    def slaw(self, args):
        """ Call slaw with ``args`` """
        cmd = ['slaw'] + args + ['--pdftotext', settings.INDIGO_PDFTOTEXT]
        self.log.info("Running %s" % cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        self.log.info("Subprocess exit code: %s, stdout=%d bytes, stderr=%d bytes" % (p.returncode, len(stdout), len(stderr)))

        return p.returncode, stdout, stderr


    def tempfile_for_upload(self, upload):
        """ Uploaded files might not be on disk. If not, create temporary file. """
        if hasattr(upload, 'temporary_file_path'):
            return upload

        f = tempfile.NamedTemporaryFile()

        self.log.info("Copying uploaded file %s to temp file %s" % (upload, f.name))
        shutil.copyfileobj(upload, f)
        f.flush()
        f.seek(0)

        return f
