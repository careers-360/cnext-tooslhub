from django.db import models
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import (
	AbstractBaseUser,
	BaseUserManager,
	PermissionsMixin,
)
from django.conf import settings
from django.urls import reverse
from django.core.validators import RegexValidator
from datetime import date
import random
from datetime import datetime
from unixtimestampfield.fields import UnixTimeStampField

from django.template.defaultfilters import slugify

from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken


class UserManager(BaseUserManager):
	def create_user(self, email, username, name, password=None):
		if not email:
			raise ValueError("Users must have an email address")

		user = self.model(
			username=username, name=name, email=self.normalize_email(email)
		)

		user.set_password(password)
		user.save(using=self._db)

		return user

	def create_superuser(self, email, username, name, password):
		user = self.create_user(
			email=email, password=password, username=username, name=name
		)
		user.is_superuser = True
		user.is_admin = True
		user.is_staff = True
		user.save(using=self._db)
		return user

	def get_user_from_token(self, token=None):
		from rest_framework_simplejwt.authentication import JWTAuthentication

		jwt = JWTAuthentication()
		jwt.get_validated_token(token)
		user = User.objects.get(id=jwt.get("user_id"))
		return user


class User(AbstractBaseUser, PermissionsMixin):
	"""
	User model extending AbstractBaseUser class with custom fields
	"""

	PHONE_NUMBER_NOT_VERIFIED = 0
	PHONE_NUMBER_VERIFIED = 1
	EMAIL_VERIFIED = 2
	PHONE_EMAIL_VERIFIED = 3
	AUTH_VERIFICATION_STATUS = (
		(PHONE_NUMBER_NOT_VERIFIED, "Phone number is not verified"),
		(PHONE_NUMBER_VERIFIED, "Phone number is verified"),
		(EMAIL_VERIFIED, "Email is verified"),
		(PHONE_EMAIL_VERIFIED, "Phone and Email are verified"),
	)

	MALE = 1
	FEMALE = 2
	OTHER = 3
	GENDER_CHOICES = (
		(MALE, "Male"), 
		(FEMALE, "Female"),
		(OTHER,"Other")
	)

	id = models.AutoField(db_column='uid', primary_key=True)

	user_type = models.CharField(max_length=255, blank=True, null=True)

	username = models.CharField(unique=True, max_length=235, blank=True, null=True)
	name = models.CharField(max_length=255, db_column='display_name')
	email = models.EmailField(unique=True,verbose_name="email address", max_length=255)

	dob = models.DateField(null=True)
	gender = models.CharField(max_length=255, blank=True, null=True)
	profile_picture = models.ImageField(upload_to="users/", blank=True, null=True)

	google_status = models.BooleanField(default=False)
	google_id = models.CharField(max_length=255, blank=True, null=True)
	facebook_status = models.BooleanField(default=False)
	facebook_id = models.IntegerField(null=True)
	truecaller_status = models.BooleanField(default=False)

	isd_code = models.IntegerField(null=False, default=91)
	phone_regex = RegexValidator(
		regex=r"^\+?1?[6789]\d{9,12}$",
		message="Please enter a valid phone number. Up to 13 digits allowed.",
	)
	phone_number = models.CharField(
		validators=[phone_regex], max_length=20, blank=True, db_index=True, db_column='mobile_number'
	)  # validators should be a list

	is_active = models.BooleanField(default=True, db_column='active')
	is_staff = models.BooleanField(default=False, db_column='staff')
	is_superuser = models.BooleanField(default=False, db_column='admin')

	
	education_stream = models.IntegerField(null=True, blank=True, db_column='education_stream')
	current_education_level = models.IntegerField(null=True, blank=True)
	current_education_passing_year = models.IntegerField(null=True, blank=True)
	twelfth_passing_year = models.IntegerField(null=True, blank=True)
	target_year = models.IntegerField(null=True, blank=True)

	school_board = models.CharField(max_length=255, blank=True, null=True)
	course_interested = models.IntegerField(null=True, blank=True)

	learn_user_id = models.IntegerField(blank=True, null=True, default=0)
	location_id = models.IntegerField(null=True, blank=True)

	about = models.TextField(blank=True, null=True)
	sf_status = models.IntegerField(default=0, null=True, blank=True)

	admission_help = models.CharField(max_length=255, blank=True, null=True)
	connect_me_whatsapp = models.IntegerField(null=True)

	user_profile_status = models.IntegerField(null=True, blank=True, default=False)

	added_on = UnixTimeStampField(auto_now_add=True, db_column='created')
	updated_on = UnixTimeStampField(auto_now=True, db_column='updated')
	last_login = UnixTimeStampField(null=True)

	paytm_user_id= models.IntegerField(blank=True, null=True, default=0)
	email_status = models.BooleanField(default=False)
	user_image_dir_path = 'users/' + str(date.today().year) + '/' + str(date.today().month) + '/' + str(date.today().day) + '/'
	mobile_verify = models.BooleanField(default=False)
	email_verify = models.BooleanField(default=False)
	email_medium = models.CharField(max_length=255, blank=True, null=True)
	manual_status = models.BooleanField(default=False)
	aspiring_stream = models.CharField(max_length=255, blank=True, null=True)
	domain_id = models.IntegerField(null=True, blank=True)
	auto_city = models.CharField(max_length=255, blank=True, null=True)
	auto_state = models.CharField(max_length=255, blank=True, null=True)
	auto_country = models.CharField(max_length=255, blank=True, null=True)
	auto_ip = models.CharField(max_length=255, blank=True, null=True)
	action_location = models.CharField(max_length=255, blank=True, null=True)
	source_url = models.CharField(max_length=255, blank=True, null=True)
	admission_preference_status = models.IntegerField(default=0)
	coaching_interested = models.BooleanField(default=False)
	
	objects = UserManager()
	USERNAME_FIELD = "email"
	REQUIRED_FIELDS = ["username", "name"]

	class Meta:
		db_table = "users"
		verbose_name_plural = "Users"
		managed = False

	def __str__(self):
		return "%s - %s" % (self.id, self.email)

	@property
	def app_token(self):
		user_token, _ = Token.objects.get_or_create(user=self)
		return user_token.key

	@property
	def token(self):
		refresh = RefreshToken.for_user(self)

		return {
			"refresh": str(refresh),
			"access": str(refresh.access_token),
		}

	def save(self, *args, **kwargs):
		if self.name and not self.username:
			self.username = slugify(self.name)
			# Append User id to make usernames unique
			self.username = self.username + "-" + str(random.randint(1, 9999))

		super(User, self).save(*args, **kwargs)
