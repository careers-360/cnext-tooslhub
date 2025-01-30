from django.db import models
from django.utils import timezone
from django.db import models
from users.models import User
from django.core.validators import RegexValidator, ValidationError, MinValueValidator, FileExtensionValidator, MaxValueValidator
from datetime import datetime, date


CURRENT_YEAR = datetime.today().year


def upload_to(instance, filename):
    return 'tools/images/{filename}'.format(filename=filename)



class UrlAlias(models.Model):
	ACTIVE = 1
	INACTIVE = 2

	STATUS_CHOICES = [
		(ACTIVE, 'Active'),
		(INACTIVE, 'In Active'),
	]

	id = models.AutoField(primary_key=True)
	url_meta_pattern_id = models.IntegerField(null=False)
	source = models.CharField(max_length=255, null=True)
	alias = models.CharField(max_length=255, null=True)
	created = models.IntegerField(("Created"), default=0)
	updated = models.IntegerField(("Updated"), default=0)
	created_by = models.IntegerField(null=False, blank=False)
	updated_by = models.IntegerField(null=False, blank=False)
	status = models.SmallIntegerField(choices=STATUS_CHOICES, null=False, blank=False)
	facet_flag = models.IntegerField(null=False, blank=False)
	push_to_sitemap = models.IntegerField(null=True, blank=True, default=1)
	h1_tag = models.CharField(max_length=255, null=True)

	class Meta:
		db_table = 'base_url_alias'
		managed = False


class UrlMetaPatterns(models.Model):
	
	STATUS_CHOICES = [
		(1, 'Active'),
		(2, 'In Active'),
	]
	id = models.AutoField(primary_key=True)
	type = models.CharField(max_length=255, null=False)
	system_url = models.CharField(max_length=255, null=False, blank=True)
	alias_pattern = models.CharField(max_length=255, null=False, blank=True)
	page_title = models.CharField(max_length=255, null=True, blank=True)
	meta_keywords = models.CharField(max_length=255, null=True, blank=True)
	meta_desc = models.TextField(max_length=255, null=True, blank=True)
	meta_abstract = models.TextField(max_length=255, null=True, blank=True)
	meta_generator = models.CharField(max_length=255, null=True, blank=True)
	meta_og_title = models.CharField(max_length=255, null=True, blank=True)
	meta_og_type = models.CharField(max_length=255, null=True, blank=True)
	meta_og_locale = models.CharField(max_length=255, null=True, blank=True)
	meta_og_site_name = models.CharField(max_length=255, null=True, blank=True)
	meta_og_image_width = models.CharField(max_length=255, null=True, blank=True)
	meta_og_image_height = models.CharField(max_length=255, null=True, blank=True)
	meta_og_description = models.TextField(max_length=255, null=True, blank=True)
	meta_og_url = models.CharField(max_length=255, null=True, blank=True)
	created = models.IntegerField(("Created"), default=0)
	updated = models.IntegerField(("Updated"), default=0)
	created_by = models.IntegerField(null=False, blank=False, default=1)
	updated_by = models.IntegerField(null=False, blank=False, default=1)
	meta_og_image = models.CharField(max_length=255, null=True, blank=True)
	twitter_card = models.CharField(max_length=255, null=True, blank=True)
	twitter_title = models.CharField(max_length=255, null=True, blank=True)
	twitter_desc = models.TextField(max_length=255, null=True, blank=True)
	twitter_url = models.CharField(max_length=255, null=True, blank=True)
	twitter_image = models.CharField(max_length=255, null=True, blank=True)
	twitter_image_width = models.CharField(max_length=255, null=True, blank=True)
	twitter_image_height = models.CharField(max_length=255, null=True, blank=True)
	status = models.SmallIntegerField(choices=STATUS_CHOICES, null=False, blank=False)
		
	class Meta:
		db_table = 'base_url_meta_pattern'
		managed = False

class CPProductCampaign(models.Model):
    type = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    alias = models.CharField(max_length=100, blank=True, null=True, default=None)
    description = models.TextField(max_length=500, blank=True, null=True, default=None)
    # aakash_input_desc = FroalaField(max_length=10000000, null=True, blank=True,
    #                          options={'toolbarButtons': ['bold', 'insertTable', 'formatUL', 'insertLink', 'html', 'insertImage', 'insertVideo'],
    #                                   'quickInsertButtons': ['table', 'ul'], 'charCounterMax': 10000000})
    # input_desc = FroalaField(max_length=10000000, null=True, blank=True,
    #                        options={'toolbarButtons': ['bold', 'insertTable', 'formatUL', 'insertLink', 'html', 'insertImage', 'insertVideo'],
    #                                 'quickInsertButtons': ['table', 'ul'], 'charCounterMax': 10000000})
    listing_desc = models.CharField(max_length=500,blank=True, null=True)
    # icon = VersatileImageField('Images', upload_to='products/', blank=True, null=True)
    image = models.ImageField(upload_to=upload_to, blank=True, null=True)
    youtube = models.CharField(max_length=255, null=True, blank=True)
    published = models.CharField(max_length=255, null=True, blank=True)
    app_status = models.CharField(max_length=255, null=True, blank=True)
    companion_mapp = models.CharField(max_length=255, null=True, blank=True)
    display_price = models.CharField(max_length=255, null=True, blank=True)
    display_coupon = models.CharField(max_length=255, null=True, blank=True)
    coupon_placeholder = models.CharField(max_length=255, null=True, blank=True)
    consume_type = models.CharField(max_length=255)
    domain = models.IntegerField(default=None, null=False, blank=True)
    currency = models.CharField(max_length=255, null=True, blank=True)
    price = models.IntegerField(default=None, null=False, blank=True)
    offer_price = models.IntegerField(default=None, null=False, blank=True)
    knockout_user_discount_percentage = models.FloatField(default=None, null=False, blank=True)
    created = models.DateTimeField(default=timezone.now, blank=True)
    created_by = models.IntegerField(default=None, null=False, blank=True)
    updated = models.DateTimeField(auto_now=True)
    updated_by = models.IntegerField(default=None, null=False, blank=True)
    total_applicant = models.IntegerField(default=0, null=False, blank=False)
    rank_type = models.CharField(max_length=10, null=True, blank=True)
    percentile_type = models.CharField(max_length=10, null=True, blank=True)
    is_landing_page = models.CharField(max_length=10, null=True, blank=True)
    # landing_page_desc = FroalaField(max_length=10000000, null=True, blank=True,
                            #  options={'toolbarButtons': ['bold', 'insertTable', 'formatUL', 'insertLink', 'html', 'insertImage', 'insertVideo'],
                            #           'quickInsertButtons': ['table', 'ul'], 'charCounterMax': 10000000})
    seo_heading = models.CharField(max_length=255, null=True, blank=True)
    seo_desc = models.TextField(max_length=600, default=None)
    parent_pid = models.ForeignKey("self", blank=True, null=True, on_delete=models.DO_NOTHING,db_column='parent_pid')
    recharge_limit = models.IntegerField(default=None, null=True, blank=True)
    recharge_pid_status = models.SmallIntegerField(default=1, null=True, blank=True)
    college_count = models.IntegerField(default=None, null=True, blank=True)
    allowed_mailer = models.IntegerField(default=3, null=True, blank=True)
    allowed_sms = models.IntegerField(default=3, null=True, blank=True)
    sms_text = models.CharField(max_length=255, null=True, blank=True)
    exam_page_pitch = models.CharField(max_length=100, null=True, blank=True)
    # rp_disclaimer = FroalaField(max_length=10000, null=True, blank=True,
    #                          options={'toolbarButtons': ['bold', 'insertTable', 'formatUL', 'insertLink', 'html',],
    #                                   'quickInsertButtons': ['table', 'ul'], 'charCounterMax': 10000})
    rp_disclaimer = models.TextField(null=True, blank=True)
    one_step_login = models.IntegerField(default=0)
    gst_include = models.IntegerField(default=0, null=False, blank=True)
    almanac_offer_price = models.IntegerField(default=0, null=False, blank=True)
    free_on_app = models.IntegerField(default=0, null=False, blank=True)
    #new fields are added below
    display_preference = models.IntegerField(null=True, blank=True)
    gif = models.FileField(upload_to='tools/gif', blank=True, null=True)
    video = models.CharField(max_length=255, null=True, blank=True)
    secondary_image = models.ImageField('Images', upload_to='tools/', blank=True, null=True)
    exam = models.IntegerField(null=True, blank=True)
    tool_system_name = models.CharField(max_length=100, null=True, blank=True)
    usage_count_matrix = models.CharField(max_length=10, null=True, blank=True)
    positive_feedback_percentage = models.FloatField(null=True, blank=True)
    for_web = models.BooleanField(default=False)
    for_app = models.BooleanField(default=False)#not used yet
    display_name_type = models.IntegerField(null=True, blank=True)
    custom_exam_name = models.CharField(max_length=255, null=True, blank=True)
    custom_flow_type = models.CharField(max_length=255, null=True, blank=True)
    custom_year = models.IntegerField(null=True, blank=True)
    listing_description = models.CharField(max_length=255, null=True, blank=True)
    exam_other_content = models.TextField(null=True, blank=True)
    exam_content_author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    header_section = models.JSONField(null=True, blank=True)
    disclaimer = models.CharField(max_length=255, null=True, blank=True)
    cp_cta_name = models.CharField(max_length=255, null=True, blank=True)
    cp_destination_url = models.CharField(max_length=255, null=True, blank=True)
    cp_pitch = models.CharField(max_length=255, null=True, blank=True)
    mapped_product_title = models.CharField(max_length=255, null=True, blank=True)
    mapped_product_cta_label = models.CharField(max_length=255, null=True, blank=True)
    mapped_product_destination_url = models.CharField(max_length=255, null=True, blank=True)
    mapped_product_pitch = models.CharField(max_length=255, null=True, blank=True)
    promotion_banner_web = models.ImageField('Images', upload_to='tools/', blank=True, null=True)
    promotion_banner_wap = models.ImageField('Images', upload_to='tools/', blank=True, null=True)
    banner_destination = models.CharField(max_length=255, null=True, blank=True)
    enable_cp_pitch_for_rp = models.BooleanField(default=False)
    cp_pitch_for_rp = models.CharField(max_length=200, null=True, blank=True)
    smart_registration = models.BooleanField(default=False)
    status = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'cp_product_campaign'
        verbose_name_plural = 'cp_product_campaign'
        db_table = 'cp_product_campaign'
        # unique_together = ('type', 'name',)
        indexes = [
            models.Index(fields=['type', ]),
            models.Index(fields=['consume_type', ]),
        ]

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.alias is None:
            self.alias = ""
        if self.description is None:
            self.description = ""
        super().save(*args, **kwargs)

class Domain(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(max_length=1023, blank=True)
    weight = models.PositiveIntegerField(null=True, blank=True)
    is_stream = models.BooleanField(default=False)
    display_status = models.BooleanField(default=False)
    old_domain_name = models.CharField(max_length=255)
    old_domain_ids = models.IntegerField(null=False, blank=False)
    published = models.CharField(max_length=255)
    created = models.DateTimeField(default=timezone.now)
    created_by = models.IntegerField(null=False, blank=False)
    updated = models.DateTimeField(default=timezone.now)
    updated_by = models.IntegerField(null=False, blank=False)
    cdn_enabled = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'domain'
        verbose_name_plural = 'domains'
        db_table = 'domain'
        ordering = ['created']
        indexes = [
            models.Index(fields=['name', ]),
            models.Index(fields=['weight', ]),
            models.Index(fields=['is_stream', ]),
            models.Index(fields=['display_status', ]),
            models.Index(fields=['published', ]),
        ]

    def __str__(self):
        return self.name



class ToolsFAQ(models.Model):
    """
    Model for storing FAQ data related to products.
    """
    product_id = models.IntegerField(verbose_name="Product ID")
    product_type = models.IntegerField(verbose_name="Product Type")
    question = models.CharField(max_length=255, verbose_name="Question")
    answer = models.TextField(verbose_name="Answer")
    status = models.BooleanField(default=True, verbose_name="Status")
    updated = models.DateTimeField(auto_now=True, verbose_name="Last Updated")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date Created")
    updated_by = models.IntegerField(verbose_name="Product ID")
    created_by = models.IntegerField(verbose_name="Product ID")
    class Meta:
        db_table = "cnext_tools_faq" #TODO change the table name 
        verbose_name = "FAQ Section"
        verbose_name_plural = "FAQ Sections"
        ordering = ["-updated"]

    def __str__(self):
        return f"FAQ {self.id}: {self.question}"
    

class Language(models.Model):
    iso_code1 = models.CharField(max_length=255, null=True, blank=True)
    iso_code2 = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "languages"
        managed = False
        verbose_name = "Language"
        verbose_name_plural = "Languages"

    def __str__(self):
        return self.name


class States(models.Model):
    name = models.CharField(max_length=255)
    country_id = models.IntegerField(null=True, blank=True)
    iso_code = models.CharField(max_length=255, null=True, blank=True)
    synonyms = models.CharField(max_length=255, null=True, blank=True)
    is_group = models.CharField(max_length=255, null=True, blank=True)
    is_ut = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'states'
        managed = False

    def __str__(self):
        return self.name
    

class College(models.Model):
	country_id=models.IntegerField(null=False, default=None)
	type_of_entity=models.IntegerField(null=False, default=None)
	sub_entity=models.IntegerField(null=True, blank=True, default=None)
	name=models.CharField(max_length=250, null=False)
	short_name=models.CharField(max_length=250, blank=True, null=True, default=None)
	entity_reference=models.IntegerField(blank=True, null=True, default=None)
	university_category=models.IntegerField(blank=True, null=True, default=None)
	specialized_in=models.IntegerField(null=True, blank=True, default=None)
	ownership=models.IntegerField(blank=True, null=True, default=None)
	institute_type_1=models.IntegerField(blank=True, null=True, default=None)
	institute_type_2=models.IntegerField(blank=True, null=True, default=None)
	year_of_establishment=models.IntegerField(blank=True, null=True, default=None)
	campus_size=models.DecimalField(decimal_places=5, max_digits=20, blank=True, null=True,
									validators=[MinValueValidator(0.01)])
	total_student_intake=models.IntegerField(blank=True, null=True)
	total_faculty=models.PositiveIntegerField(blank=True, null=True)
	# remark_1=FroalaField(max_length=2, blank=True,
	# 					 options={'toolbarButtons': ['bold', 'insertTable', 'formatUL', 'insertLink'],
	# 							  'quickInsertButtons': ['table', 'ul'], 'charCounterMax': 10000000})
	# about_college=FroalaField(max_length=2, blank=True, null=True,
	# 						  options={'toolbarButtons': ['bold', 'insertTable', 'formatUL', 'insertLink'],
	# 								   'quickInsertButtons': ['table', 'ul'], 'charCounterMax': 10000000})
	website_url=models.URLField(max_length=255, blank=True, null=True)
	contact_number_1=models.CharField(max_length=35, blank=True, null=True)
	contact_number_2=models.CharField(max_length=35, blank=True, null=True)
	email_1=models.EmailField(max_length=155, blank=True, null=True)
	email_2=models.EmailField(max_length=155, blank=True, null=True)
	address_of_campus=models.CharField(max_length=1000, blank=True, null=True)
	zip_code=models.PositiveIntegerField(blank=True, null=True)
	relate_to=models.CharField(max_length=255, blank=True, null=True)
	total_enrollments=models.PositiveIntegerField(blank=True, null=True)
	college_type=models.CharField(max_length=55, default='normal')
	published=models.CharField(max_length=255)
	# remark_2=FroalaField(max_length=1000, null=True, blank=True,
	# 					 options={'toolbarButtons': ['bold', 'insertTable', 'formatUL', 'insertLink'],
	# 							  'quickInsertButtons': ['table', 'ul'], 'charCounterMax': 10000000})
	added_on=models.DateTimeField(db_column='created', auto_now_add=True)
	updated_on=models.DateTimeField(db_column='updated', auto_now=True)
	created_by=models.IntegerField(default=None, null=False, blank=False)
	updated_by=models.IntegerField(default=None, null=False, blank=False)
	old_nid=models.IntegerField(blank=True, null=True)
	google_json=models.TextField(null=True, blank=True)
	google_json_hindi=models.TextField(null=True, blank=True)
	general_info_map=models.ImageField(
		upload_to='colleges/staticmap/' + str(date.today().year) + '/' + str(date.today().month) + '/' + str(
			date.today().day) + '/',
		null=True,
		default=None
	)
	location_id=models.IntegerField(default=None, null=False, blank=False)
	admission_phone=models.CharField(max_length=35, blank=True, null=True)
	former_name=models.CharField(max_length=250, blank=True, null=True, default=None)
	reviewed_on=models.DateTimeField(null=True, blank=True)
	reviewed_by=models.IntegerField(default=None, null=False, blank=False)
	unpublish_category=models.IntegerField(default=None, null=True, blank=True)
	unpublish_reason_text=models.TextField(max_length=100000, default=None, null=True, blank=True)
	merged_into_college_id=models.IntegerField(default=None, null=True, blank=True)
	push_to_google=models.BooleanField(default=False)
	push_to_google_hindi = models.BooleanField(default=False)
	top_college=models.PositiveIntegerField(default=None, null=True, blank=True)
	unpublish_timestamp=models.DateTimeField(default=None, null=True, blank=True)
	official_college_name=models.CharField(max_length=250, blank=True, null=True, default=None)
	is_top=models.BooleanField(default=False)
	adm_client=models.IntegerField(default=0, null=False, blank=False)
	push_to_paytm=models.BooleanField(default=False)
	placement_status=models.IntegerField(default=0, null=True, blank=True)
	is_hospital=models.IntegerField(default=0)
	status=models.BooleanField(default=True)
	push_to_search=models.BooleanField(default=True)
	popular_stream=models.IntegerField(default=None, null=True, blank=True)
	seo_name=models.CharField(max_length=250, blank=True, null=True)
	
	class Meta:
		verbose_name='college'
		verbose_name_plural='colleges'
		db_table='colleges'
		indexes=[
			models.Index(fields=['name', ]),
			models.Index(fields=['short_name', ]),
			models.Index(fields=['entity_reference', ]),
			models.Index(fields=['university_category', ]),
			models.Index(fields=['ownership', ]),
			models.Index(fields=['year_of_establishment', ]),
			models.Index(fields=['total_student_intake', ]),
			models.Index(fields=['published', ]),
			models.Index(fields=['relate_to', ]),
			models.Index(fields=['zip_code', ]),
			models.Index(fields=['college_type', ]),
			models.Index(fields=['push_to_search', ]),
		]
		managed=False
	
	def __str__(self):
		return self.name


class Branches(models.Model):
	name=models.CharField(max_length=255, unique=True, null=False)
	company_id=models.IntegerField()
	certificate_id=models.IntegerField()
	syllabus_id=models.IntegerField()
	default_domain=models.ForeignKey(Domain, on_delete=models.DO_NOTHING, default=None,
									 related_name="branch_default_domain")
	no_of_hits=models.IntegerField(null=True, default=None, blank=True)
	relate_to=models.CharField(max_length=255, blank=True, null=True)
	image=models.ImageField('Images', upload_to='branches/', blank=True, null=True)
	old_nids=models.CharField(max_length=255, unique=True, null=False)
	published=models.CharField(max_length=255)
	added_on=models.DateTimeField(db_column='created', auto_now_add=True)
	updated_on=models.DateTimeField(db_column='updated', auto_now=True)
	created_by=models.IntegerField(null=True)
	updated_by=models.IntegerField(null=True)
	page_title=models.CharField(max_length=255, blank=True, null=True, default=None)
	page_description=models.TextField(max_length=500, blank=True, null=True, default=None)
	branches_keywords=models.TextField(max_length=500, blank=True, null=True, default=None)
	download_count=models.IntegerField(null=True)
	# upcoming_trends_topics=FroalaField(max_length=10000000, null=True, blank=True, default=None, options={
	# 	'toolbarButtons': ['bold', 'italic', 'insertTable', 'formatOL', 'formatUL', 'insertLink', 'paragraphFormat'],
	# 	'quickInsertButtons': ['table', 'ul'], 'paragraphFormat': {'H3': 'Heading 3'}})
	branch_pdf_path=models.CharField(max_length=255, blank=True, null=True, default=None)
	
	class Meta:
		verbose_name="branch"
		verbose_name_plural="branches"
		db_table="branches"
		indexes=[
			models.Index(fields=['published', ]),
		]
		managed=False
	
	# string representation of branches
	def __str__(self):
		return self.name


class Degrees(models.Model):
	name=models.CharField(unique=True, max_length=255, null=False)
	full_name=models.CharField(max_length=255, null=True, blank=True)
	# description=FroalaField(max_length=10000000,
	# 						options={'toolbarButtons': ['bold', 'insertTable', 'formatUL', 'insertLink'],
	# 								 'quickInsertButtons': ['table', 'ul']}, null=True, blank=True, default=None)
	weight=models.PositiveIntegerField(null=True, blank=True)
	education_level=models.ForeignKey('PreferredEducationLevel', models.DO_NOTHING)
	domain=models.ManyToManyField(Domain)
	published=models.CharField(max_length=255)
	added_on=models.DateTimeField(db_column='created', auto_now_add=True)
	created_by=models.IntegerField(null=False, blank=False)
	updated_on=models.DateTimeField(db_column='updated', auto_now=True)
	updated_by=models.IntegerField(null=False, blank=False)
	# eligibility_criteria=FroalaField(max_length=10000000, null=True, blank=True, default=None,
	# 								 options={'toolbarButtons': ['bold', 'insertTable', 'formatUL', 'insertLink'],
	# 										  'quickInsertButtons': ['table', 'ul']})
	# scope=FroalaField(max_length=10000000, null=True, blank=True, default=None,
	# 				  options={'toolbarButtons': ['bold', 'insertTable', 'formatUL', 'insertLink'],
	# 						   'quickInsertButtons': ['table', 'ul']})
	primary_degree=models.BooleanField(default=False)
	
	class Meta:
		verbose_name="degree"
		verbose_name_plural="degrees"
		db_table="degrees"
		managed=False
		
	def __str__(self):
		return self.name


class PreferredEducationLevel(models.Model):
	name=models.CharField(max_length=255, null=False, unique=True, default=None)
	parent_id=models.IntegerField(default=False)
	
	class Meta:
		db_table='preferred_education_levels'
		verbose_name='Preferred Education Level'
		verbose_name_plural='Preferred Education Levels'
		managed=False
		indexes=[
			models.Index(fields=['name', ]),
			models.Index(fields=['parent_id', ]),
		]
	
	def __str__(self):
		return self.name
      

class ExamClassification(models.Model):
    exam_type = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'exam_classification'
        verbose_name = 'exam_classifications'
        verbose_name_plural = 'exam_classifications'

class Exam(models.Model):
    """
    Model for the Basic Details Tab of Exam
    """

    exam_name = models.CharField(max_length=255)
    exam_short_name = models.CharField(max_length=255, blank=True)
    instance_month = models.IntegerField(null=True, blank=True, default=0)
    instance_year = models.PositiveIntegerField(default=CURRENT_YEAR)
    exam_category = models.CharField(max_length=255, blank=True)
    type_of_exam = models.CharField(max_length=255, blank=True)
    exam_reference = models.CharField(max_length=255, null=True, blank=True)
    exam_conducting_body = models.CharField(max_length=255, null=True, blank=True)
    ecb_logo = models.ImageField(upload_to="exam_pics/", null=True, blank=True)
    exam_featured_image = models.ImageField(
        upload_to="exam_pics/featured/", null=True, blank=True
    )
    status = models.CharField(max_length=255, null=True, blank=True)
    domain = models.ForeignKey(
        Domain, on_delete=models.DO_NOTHING, null=True, blank=True, related_name="exams"
    )
    created = models.DateTimeField(default=timezone.now, blank=True)
    created_by = models.IntegerField(default=None, null=False, blank=True)
    updated = models.DateTimeField(default=timezone.now, blank=True)
    updated_by = models.IntegerField(default=None, null=False, blank=True)
    push_to_google = models.BooleanField(default=False)
    push_to_google_hindi = models.BooleanField(default=False)

    google_json=models.TextField(null=True, blank=True)
    google_json_hindi=models.TextField(null=True, blank=True)
    
    old_name = models.CharField(max_length=255, null=True, blank=True)
    adm_client = models.IntegerField(null=False, blank=True, default=0)
    google_json = models.TextField(null=True, blank=True)
    is_preparation = models.BooleanField(default=0)
    exam_classification = models.ForeignKey("ExamClassification", db_column="exam_classification", on_delete=models.DO_NOTHING)

    def validate_file_extension(value):
        """
        Validation on the file type to be uploaded (here: pdf)
        """
        if not value.name.endswith(".pdf"):
            raise ValidationError("Upload only pdf files.")

    exam_brochure = models.FileField(
        upload_to="private/brochures/exam_brochure_uploaded/{}/{}/{}/".format(
            datetime.today().year, datetime.today().month, datetime.today().day
        ),
        validators=[validate_file_extension],
        null=True,
        max_length=255,
        blank=True,
    )
    preferred_education_level_id = models.IntegerField(
        null=True, default=None, blank=True
    )
    freq_of_conduct = models.CharField(max_length=255, null=True, blank=True)
    exam_result_validity = models.IntegerField(null=True, blank=True)
    state_of_exam = models.ForeignKey(
        States, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    competition_type = models.CharField(max_length=255, null=True, blank=True)
    no_of_seats = models.PositiveIntegerField(null=True, blank=True)
    exam_duration = models.CharField(max_length=255, blank=True, null=True)
    parent_exam_id = models.PositiveIntegerField(default=0, null=True, blank=True)
    ling_medium_of_exam = models.ManyToManyField(
        Language, related_name="exams", blank=True, db_table="exam_medium_mapping"
    )
    synonyms_id = models.IntegerField()
    counselling_grading_type = models.CharField(max_length=255, null=True, blank=True)
    instance_id = models.IntegerField(null=True, default=None, blank=True)
    super_parent_id = models.IntegerField(null=True, default=None, blank=True)
    exam_of_counselling = models.ManyToManyField(
        "self",
        related_name="exams",
        blank=True,
        db_table="counselling_exam_mapping",
        symmetrical=False,
    )
    next_in_series = models.IntegerField(null=True, blank=True, default=None)
    old_nid = models.IntegerField(null=True, default=None, blank=True)
    created_brochure = models.CharField(max_length=255, null=True, blank=True)
    admission_year = models.IntegerField(blank=True, null=True, default=None)
    closing_status = models.IntegerField(blank=True, null=True, default=0)
    reviewed = models.DateTimeField(default=timezone.now, blank=True)
    unpublished_reason = models.CharField(max_length=255, blank=True, null=True)
    unpublished_reason_other = models.CharField(max_length=255, blank=True, null=True)
    parent_sub_exam_id = models.IntegerField(null=True, default=None, blank=True)
    syllabus_url = models.URLField(null=True, blank=True)
    exam_center_url = models.URLField(null=True, blank=True)
    exam_dates_url = models.URLField(null=True, blank=True)
    unpublish_timestamp = models.DateTimeField(default=None, blank=True)
    push_topics = models.SmallIntegerField(default=None, blank=True)
    push_to_paytm = models.BooleanField(default=False)
    move_to_top = models.BooleanField(default=False)
    author = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, blank=True, related_name="exams")
    move_to_top_order = models.IntegerField(blank=True, null=True, default=0)

    class Meta:
        db_table = "exams"
        verbose_name = "Exam"
        verbose_name_plural = "Exams"
        managed = False
        indexes = [
            models.Index(
                fields=[
                    "exam_name",
                ]
            ),
            models.Index(
                fields=[
                    "exam_short_name",
                ]
            ),
            models.Index(
                fields=[
                    "exam_reference",
                ]
            ),
            models.Index(
                fields=[
                    "exam_category",
                ]
            ),
            models.Index(
                fields=[
                    "type_of_exam",
                ]
            ),
            models.Index(
                fields=[
                    "preferred_education_level_id",
                ]
            ),
            models.Index(
                fields=[
                    "status",
                ]
            ),
            models.Index(
                fields=[
                    "parent_exam_id",
                ]
            ),
            models.Index(
                fields=[
                    "super_parent_id",
                ]
            ),
        ]

    @property
    def display_name(self):
        exam_type = self.type_of_exam
        display_name = self.exam_short_name if self.exam_short_name else self.exam_name
        if exam_type == "":
            parentexam_id = self.parent_exam_id
            parent_exam = Exam.objects.only('exam_short_name', 'exam_name').get(id=parentexam_id)
            if parent_exam.exam_short_name:
                display_name = "%s %s" % (parent_exam.exam_short_name, self.exam_name)
            else:
                display_name = "%s %s" % (parent_exam.exam_name, self.exam_name)

        return display_name

    def __str__(self):
        return self.exam_name
    
class RecommendedCollegeManager(models.Manager):
	def get_queryset(self):
		return super().get_queryset().values('college_id__name', 'college_id', 'college_id__location_id',
											 'college_id__ownership').distinct()

class CollegeCourse(models.Model):
	course_name=models.CharField(max_length=255, null=False, default=None)
	college=models.ForeignKey('College', models.DO_NOTHING, null=True, blank=True)
	degree_offered_college_id=models.IntegerField(null=True, default=None)
	degree=models.ForeignKey('Degrees', models.DO_NOTHING)
	branch=models.ForeignKey('Branches', models.DO_NOTHING)
	exam=models.ManyToManyField(Exam, related_name="exam_id", blank=True)
	level=models.IntegerField(null=False)  # choices from college_examination_level
	study_mode=models.IntegerField(null=True, default=None, blank=True)
	course_duration=models.FloatField(null=True, default=None, blank=True)
	approved_intake=models.PositiveIntegerField(null=True, default=None, blank=True)
	# course_details=FroalaField(null=True, blank=True,
	# 						   options={'toolbarButtons': ['bold', 'insertTable', 'formatUL', 'insertLink'],
	# 									'quickInsertButtons': ['table', 'ul']})
	# eligibility_criteria=FroalaField(null=True, blank=True,
	# 								 options={'toolbarButtons': ['bold', 'formatUL', 'insertLink'],
	# 										  'quickInsertButtons': ['table', 'ul']})
	# admission_procedure=FroalaField(null=True, blank=True,
	# 								options={'toolbarButtons': ['bold', 'formatUL', 'insertLink'],
	# 										 'quickInsertButtons': ['table', 'ul']})
	sort_order=models.IntegerField(null=True, default=None, blank=True)
	no_fresh_admission=models.PositiveIntegerField(null=True, default=None, blank=True)
	published=models.CharField(max_length=255)
	# other_detail_fees=FroalaField(null=True, blank=True,
	# 							  options={'toolbarButtons': ['bold', 'insertTable', 'formatUL', 'insertLink'],
	# 									   'quickInsertButtons': ['table', 'ul']})
	added_on=models.DateTimeField(db_column='created', auto_now_add=True)
	updated_on=models.DateTimeField(db_column='updated', auto_now=True)
	created_by=models.IntegerField(default=None, null=False, blank=False)
	updated_by=models.IntegerField(default=None, null=False, blank=False)
	status=models.BooleanField(default=True)
	degree_domain=models.PositiveIntegerField(null=True)
	old_course_nid=models.IntegerField(blank=True, null=True)
	brochure_pdf_path=models.CharField(max_length=255, null=True, blank=True, default=None)
	dummy_course_url=models.CharField(max_length=1000, default=None, null=True)
	reviewed_on=models.DateTimeField(null=True, blank=True)
	reviewed_by=models.IntegerField(default=None, null=False, blank=False)
	unpublish_category=models.IntegerField(default=None, null=True, blank=True)
	unpublish_reason_text=models.TextField(max_length=100000, default=None, null=True, blank=True)
	unpublish_timestamp=models.DateTimeField(default=None, null=True, blank=True)
	# remark=FroalaField(max_length=1000, null=True, blank=True,
	# 				   options={'toolbarButtons': ['bold', 'insertTable', 'formatUL', 'insertLink'],
	# 							'quickInsertButtons': ['table', 'ul'], 'charCounterMax': 10000000})
	placement_status=models.IntegerField(default=0, null=True, blank=True)
	credential=models.PositiveIntegerField(null=True, default=None, blank=True)
	learning_efforts_type=models.PositiveIntegerField(null=True, default=None, blank=True)
	efforts_start=models.PositiveIntegerField(null=True, default=None, blank=True)
	efforts_end=models.PositiveIntegerField(null=True, default=None, blank=True)
	course_credits=models.FloatField(null=True, default=None, blank=True)
	
	push_to_google=models.BooleanField(default=False)
	push_to_google_hindi = models.BooleanField(default=False)

	google_json=models.TextField(null=True, blank=True)
	google_json_hindi=models.TextField(null=True, blank=True)

	objects=models.Manager()
	recommended_colleges=RecommendedCollegeManager()
	created_brochure_status=models.BooleanField(default=False)
	created_brochure=models.CharField(max_length=255)
	move_to_top=models.IntegerField(default=0, null=False, blank=False)
	degree_domain_sa_stream_map_id = models.IntegerField(null=True, blank=True)
	
	class Meta:
		verbose_name='college course'
		verbose_name_plural='college courses'
		db_table='colleges_courses'
		indexes=[
			models.Index(fields=['course_name', ]),
			models.Index(fields=['degree_offered_college_id', ]),
			models.Index(fields=['level', ]),
			models.Index(fields=['study_mode', ]),
			models.Index(fields=['approved_intake', ]),
			models.Index(fields=['sort_order', ]),
			models.Index(fields=['no_fresh_admission', ]),
			models.Index(fields=['published', ]),
		]
		managed=False
	
	def __str__(self):
		return self.course_name


class CPFeedback(models.Model):
    id = models.AutoField(primary_key=True)
    is_moderated = models.SmallIntegerField(default=0, null=False, blank=True)
    feedback_type = models.CharField(max_length=100,null=False, blank=True)
    exam_id = models.CharField(max_length=255, null=True, blank=True)
    counselling_id = models.CharField(max_length=255, null=True, blank=True)
    session_id = models.IntegerField(null=True, blank=True)
    product_id = models.CharField(max_length=255, null=True, blank=True)
    response_type = models.CharField(max_length=255, null=True, blank=True)
    complement = models.CharField(max_length=255, null=True, blank=True)
    msg = models.CharField(max_length=255, null=True, blank=True)
    gd_chance_count = models.IntegerField(null=True, blank=True)
    tf_chance_count = models.IntegerField(null=True, blank=True)
    maybe_chance_count = models.IntegerField(null=True, blank=True)
    counselling_change = models.IntegerField(default=0, blank=True, null=True)
    user_type = models.CharField(max_length=255, default='Careers360', blank=False)
    device = models.CharField(max_length=255, null=True, blank=True)
    user_name = models.CharField(max_length=255, null=True, blank=True)
    user_image = models.ImageField(upload_to='tools/images/', blank=True, null=True)
    custom_feedback = models.TextField(null=True, blank=True)
    updated = models.DateTimeField(default=timezone.now, blank=True)
    created = models.DateTimeField(default=timezone.now, blank=True)
    updated_by = models.IntegerField(default=None, null=False, blank=True)
    created_by = models.IntegerField(default=None, null=False, blank=True)

    class Meta:
        verbose_name = 'cp_feedback'
        verbose_name_plural = 'cp_feedback'
        db_table = 'cp_feedback'

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()

        super(CPFeedback, self).save(*args, **kwargs)

class CasteCategory(models.Model):
    parent_id = models.PositiveIntegerField(null=True, blank=True)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(max_length=1023, blank=True)
    published = models.CharField(max_length=255, null=True, blank=True)
    created = models.DateTimeField(default=timezone.now, blank=True)
    created_by = models.IntegerField(default=None, null=False, blank=True)
    updated = models.DateTimeField(default=timezone.now, blank=True)
    updated_by = models.IntegerField(default=None, null=False, blank=True)

    class Meta:
        verbose_name = 'cp_caste'
        verbose_name_plural = 'cp_caste'
        db_table = 'cp_caste'
        indexes = [
            models.Index(fields=['parent_id', ]),
            models.Index(fields=['name', ]),
        ]

    def __str__(self):
        return self.name
    

class DisabilityCategory(models.Model):
    parent_id = models.PositiveIntegerField(null=True, blank=True)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(max_length=1023, blank=True)
    published = models.CharField(max_length=255, null=True, blank=True)
    created = models.DateTimeField(default=timezone.now, blank=True)
    created_by = models.IntegerField(default=None, null=False, blank=True)
    updated = models.DateTimeField(default=timezone.now, blank=True)
    updated_by = models.IntegerField(default=None, null=False, blank=True)

    class Meta:
        verbose_name = 'cp_disability'
        verbose_name_plural = 'cp_disability'
        db_table = 'cp_disability'
        indexes = [
            models.Index(fields=['parent_id', ]),
            models.Index(fields=['name', ]),
        ]

class UserGroups(models.Model):
    """
    User Groups model using for the mapping between users and groups
    """
    user = models.ForeignKey('users.User', models.DO_NOTHING)
    group = models.ForeignKey('Groups', models.DO_NOTHING)
    status = models.BooleanField(default=False)

    class Meta:
        db_table = 'user_groups'
        unique_together = (('user', 'group'),)

class Groups(models.Model):
    """
    Groups model with name & status attributes
    """
    name = models.CharField(max_length=255)
    status = models.BooleanField(default=False)

    class Meta:
        db_table = 'groups'

class UserPermissions(models.Model):
    """
    User Permission Model using for the mapping between users and permissions
    """
    user = models.ForeignKey('users.User', models.DO_NOTHING)
    permission = models.ForeignKey('Permissions', models.DO_NOTHING)
    status = models.BooleanField(default=False)

    class Meta:
        db_table = 'user_permissions'
        unique_together = (('user', 'permission'),)


class Permissions(models.Model):
    """
    Permissions model with name, codename, content_type & status attributes
    """
    name = models.CharField(max_length=255)
    codename = models.CharField(max_length=100)
    content_type = models.CharField(max_length=255)
    status = models.BooleanField(default=False)

    class Meta:
        db_table = 'permissions'
        ordering = ['id']




class CPTopCollege(models.Model):
    exam_id = models.IntegerField(null=True, blank=True)
    college_id = models.IntegerField(null=True, blank=True)
    college_name = models.CharField(max_length=255, null=True, blank=True)
    college_short_name = models.CharField(max_length=255, null=True, blank=True)
    college_url = models.CharField(max_length=255, null=True, blank=True)
    review_count = models.IntegerField(null=True, blank=True)
    aggregate_rating = models.FloatField(null=True, blank=True)
    course_id = models.IntegerField(null=True, blank=True)
    course_name = models.CharField(max_length=255, null=True, blank=True)
    course_url = models.CharField(max_length=255, null=True, blank=True)
    final_cutoff = models.FloatField(null=True, blank=True)
    rank_type = models.CharField(max_length=255, null=True, blank=True)
    process_type = models.CharField(max_length=255, null=True, blank=True)
    status = models.IntegerField(null=True, blank=True)
    submenu_data = models.TextField(null=True, blank=True)
    class Meta:
        db_table = 'cp_top_college'

class ProductSession(models.Model):
    product_id = models.IntegerField(null=False, blank=False)
    session_start_date = models.DateTimeField(null=False, blank=False)
    session_end_date = models.DateTimeField(null=False, blank=False)
    session_peak_start_date = models.DateTimeField(null=False, blank=False)
    session_peak_end_date = models.DateTimeField(null=False, blank=False)
    created_by = models.IntegerField(null=False, blank=False)
    created = models.DateTimeField(null=False, blank=False)
    updated = models.DateTimeField(null=False, blank=False)

    class Meta:
        db_table = 'product_session'