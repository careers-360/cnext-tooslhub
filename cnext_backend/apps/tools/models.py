from django.db import models
from django.utils import timezone
from django.db import models
from users.models import User
def upload_to(instance, filename):
    return 'tools/images/{filename}'.format(filename=filename)

class CPProductCampaign(models.Model):
    type = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    alias = models.CharField(max_length=100)
    # description = models.TextField(max_length=500, blank=True, null=True, default=None)
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
    updated = models.DateTimeField(default=timezone.now, blank=True)
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
    gif = models.CharField(max_length=255, null=True, blank=True)
    video = models.CharField(max_length=255, null=True, blank=True)
    secondary_image = models.ImageField('Images', upload_to='tools/', blank=True, null=True)
    exam = models.IntegerField(null=True, blank=True)
    tool_system_name = models.CharField(max_length=100, null=True, blank=True)
    usage_count_matrix = models.CharField(max_length=10, null=True, blank=True)
    positive_feedback_per = models.FloatField(null=True, blank=True)
    for_web = models.BooleanField(default=False)
    for_app = models.BooleanField(default=False)
    display_name_type = models.IntegerField(null=True, blank=True)
    custom_exam_name = models.CharField(max_length=255, null=True, blank=True)
    custom_flow_type = models.CharField(max_length=255, null=True, blank=True)
    custom_year = models.IntegerField(null=True, blank=True)
    listing_description = models.CharField(max_length=255, null=True, blank=True)
    exam_other_content = models.TextField(null=True, blank=True)
    header_section = models.JSONField(null=True, blank=True)
    desclaimer = models.CharField(max_length=255, null=True, blank=True)
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
    

class Domain(models.Model):
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
        db_table = "cnext_tools_faq_section" #TODO change the table name 
        verbose_name = "FAQ Section"
        verbose_name_plural = "FAQ Sections"
        ordering = ["-updated"]

    def __str__(self):
        return f"FAQ {self.id}: {self.question}"
