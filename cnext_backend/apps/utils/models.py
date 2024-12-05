from django.db import models
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.conf import settings
from utils.managers import SoftDeletableManager
from froala_editor.fields import FroalaField


class SourceMixin(models.Model):
	"""
	Source Stamped Model
	An abstract base class model that provides default
	``first_source`` and ``last_source`` fields .
	"""
	first_source = models.CharField(null=True, blank=True,max_length=255)
	last_source = models.CharField(null=True, blank=True,max_length=255)

	class Meta:
		abstract = True


class SourceIDMixin(models.Model):
	"""
	Source Stamped Model
	An abstract base class model that provides default
	``first_source`` and ``last_source`` fields .
	"""
	first_source_id = models.IntegerField()
	last_source_id = models.IntegerField()

	class Meta:
		abstract = True

class CronTask(models.Model):
	name = models.CharField(max_length=255)
	start_on = models.DateTimeField()
	end_on = models.DateTimeField(null=True, blank=True)
	output = models.TextField(null=True, blank=True)

	class Meta:
		db_table = 'cnext_cron_task'
		verbose_name_plural = 'Cron Tasks'

	def __str__(self):
		return '%s - %s' % (self.id, self.name)


class TimeMixin(models.Model):
	"""
	TimeStamped Model
	An abstract base class model that provides default
	``added_on`` and ``updated_on`` fields.
	"""
	added_on = models.DateTimeField(auto_now_add=True)
	updated_on = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True


class AuthMixin(models.Model):
	"""
	Auth Stamped Model
	An abstract base class model that provides default
	``added_by`` and ``updated_by`` fields.
	"""
	added_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="%(app_label)s_%(class)s_added_by")
	updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="%(app_label)s_%(class)s_updated_by")

	class Meta:
		abstract = True


class SoftDeleteMixin(models.Model):
	"""
	An abstract base class model with a ``is_deleted`` field that
	marks entries that are not going to be used anymore, but are
	kept in db for any reason.
	Default manager returns only not-removed entries.
	"""
	is_deleted = models.BooleanField(default=False)
	deleted_on = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True

	objects = SoftDeletableManager()

	def delete(self, using=None, soft=True, *args, **kwargs):
		"""
		Soft delete object (set its ``is_deleted`` field to True).
		Actually delete object if setting ``soft`` to False.
		"""
		if soft:
			self.is_deleted = True
			self.save(using=using)
		else:
			return super(SoftDeleteMixin, self).delete(using=using, *args, **kwargs)

class CustomFroalaField(FroalaField):
    
    def __init__(self, *args, **kwargs):
        toolbarButtons = kwargs.pop('toolbarButtons', [
            'bold',
            'italic',
            'underline',
            'color',
            'paragraphFormat',
            'paragraphStyle',
            'alignLeft',
            'alignCenter',
            'alignRight',
            'alignJustify',
            'formatOLSimple',
            'quote',
            'insertLink',
            'insertImage',
            'insertVideo',
            'insertTable',
            'insertFile',
            'insertHR',
            'selectAll',
            'clearFormatting',
            'help',
            'html',
            'undo',
            'redo',
            'fullscreen',
        ])
        quickInsertButtons = kwargs.pop('quickInsertButtons', ['image', 'video', 'embedly', 'table', 'hr'])
        charCounterMax = kwargs.pop('charCounterMax', 10000000)
        placeholderText = kwargs.pop('placeholderText', "Type something")
        heightMin = kwargs.pop('heightMin', 150)
        addTagCareer = kwargs.pop('addTagCareer', False)
        super().__init__(*args, **kwargs)

        if addTagCareer:
            toolbarButtons.append('tagCareer')

        self.max_length=2,
        self.blank=True,
        self.null=True,
        self.options={
            'toolbarButtons': toolbarButtons,
            'quickInsertButtons': quickInsertButtons,
            'charCounterMax': charCounterMax,
            'placeholderText': placeholderText,
            'heightMin': heightMin,
            'imageEditButtons': ['imageReplace', 'imageCaption', 'imageRemove', '|', 'imageLink', 'linkOpen', 'linkEdit', 'linkRemove', '-', 'imageDisplay', 'imageStyle', 'imageAlt', 'imageSize'],
            'videoEditButtons': ['videoReplace', 'videoRemove', '|', 'videoDisplay', 'videoSize'],
            'imageUploadURL': '/dj-admin/career/froala_editor/validate_image_upload/',
            'pastePlain': False,
            'colorsText': ['#F1935C', '#000000', 'REMOVE'],
            'colorsBackground': [],
            'colorsHEXInput': False
        }