from django.db import models
from django.utils import timezone

class RpMeritSheet(models.Model):
    product_id = models.IntegerField(null=True, blank=True)
    product_type = models.IntegerField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    to_graph = models.BooleanField(default=False)
    status = models.BooleanField(default=True)
    created = models.DateTimeField(null=True, blank=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated = models.DateTimeField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "cnext_rp_merit_sheet"
        verbose_name = "cnext_rp_merit_sheet"
        verbose_name_plural = "Merit Sheets"


class RpMeanSd(models.Model):
    product_id = models.IntegerField(null=True, blank=True)
    product_type = models.IntegerField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    input_flow_type = models.IntegerField(null=True, blank=True)
    sheet_mean = models.FloatField(null=True, blank=True)
    sheet_sd = models.FloatField(null=True, blank=True)
    admin_mean = models.FloatField(null=True, blank=True)
    admin_sd = models.FloatField(null=True, blank=True)
    status = models.BooleanField(default=True)
    created = models.DateTimeField(null=True, blank=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated = models.DateTimeField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "cnext_rp_mean_sd"
        verbose_name = "Mean and Standard Deviation"
        verbose_name_plural = "Means and Standard Deviations"



class RpSmartRegistration(models.Model):
    product_id = models.IntegerField(null=True, blank=True)
    product_type = models.IntegerField(null=True, blank=True)
    field = models.IntegerField(null=True, blank=True)
    peak_session = models.BooleanField(default=False)
    non_peak_session = models.BooleanField(default=False)
    status = models.BooleanField(default=True)
    created = models.DateTimeField(null=True, blank=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated = models.DateTimeField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "cnext_rp_smart_registration"
        verbose_name = "Smart Registration"
        verbose_name_plural = "Smart Registrations"
    

class RpInputFlowMaster(models.Model):
    input_flow_type = models.CharField(max_length=255, null=True, blank=True)
    input_type = models.CharField(max_length=255, null=True, blank=True)
    input_process_type = models.CharField(max_length=255, null=True, blank=True)
    status = models.BooleanField(default=True)
    created = models.DateTimeField(null=True, blank=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated = models.DateTimeField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "cnext_rp_input_flow_master"
        verbose_name = "Input Flow Master"
        verbose_name_plural = "Input Flow Masters"


class RpMeritList(models.Model):
    product_id = models.IntegerField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    caste = models.IntegerField(null=True, blank=True)
    disability = models.IntegerField(null=True, blank=True)
    slot = models.IntegerField(null=True, blank=True)
    difficulty_level = models.IntegerField(null=True, blank=True)
    input_flow_type = models.IntegerField(null=True, blank=True)
    input_value = models.FloatField(null=True, blank=True)
    z_score = models.FloatField(null=True, blank=True)
    result_flow_type = models.IntegerField(null=True, blank=True)
    result_value = models.FloatField(null=True, blank=True)
    status = models.BooleanField(default=True)
    created = models.DateTimeField(null=True, blank=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated = models.DateTimeField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "cnext_rp_merit_list"
        verbose_name = "Merit List"
        verbose_name_plural = "Merit Lists"

class RpResultFlowMaster(models.Model):
    result_flow_type = models.CharField(max_length=255, null=True, blank=True)
    result_type = models.CharField(max_length=255, null=True, blank=True)
    result_process_type = models.CharField(max_length=255, null=True, blank=True)
    status = models.BooleanField(default=True)
    created = models.DateTimeField(null=True, blank=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated = models.DateTimeField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "cnext_rp_result_flow_master"
        verbose_name = "Result Flow Master"
        verbose_name_plural = "Result Flow Masters"

class RpContentSection(models.Model):
    product_id = models.IntegerField(null=True, blank=True)
    product_type = models.IntegerField(null=True, blank=True)
    heading = models.CharField(max_length=255, null=True, blank=True)
    content = models.CharField(max_length=255, null=True, blank=True)
    image_web = models.CharField(max_length=255, null=True, blank=True)
    image_wap = models.CharField(max_length=255, null=True, blank=True)
    status = models.BooleanField(default=True)
    created = models.DateTimeField(null=True, blank=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated = models.DateTimeField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "cnext_rp_content_section"
        verbose_name = "Content Section"
        verbose_name_plural = "Content Sections"


class RpFormField(models.Model):
    product_id = models.IntegerField(null=True, blank=True)
    product_type = models.IntegerField(null=True, blank=True)
    field_type = models.IntegerField(null=True, blank=True)
    input_flow_type = models.IntegerField(null=True, blank=True)
    display_name = models.CharField(max_length=255, null=True, blank=True)
    place_holder_text = models.CharField(max_length=255, null=True, blank=True)
    error_message = models.CharField(max_length=255, null=True, blank=True)
    min_val = models.FloatField(null=True, blank=True)
    max_val = models.FloatField(null=True, blank=True)
    weight = models.IntegerField(null=True, blank=True)
    mapped_process_type = models.IntegerField(null=True, blank=True)
    mandatory = models.BooleanField(default=False)
    status = models.BooleanField(default=True)
    created = models.DateTimeField(null=True, blank=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated = models.DateTimeField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "cnext_rp_form_field"
        verbose_name = "Form Field"
        verbose_name_plural = "Form Fields"

class RpVariationFactor(models.Model):
    rp_id = models.IntegerField(null=True, blank=True)
    lower_value = models.FloatField(null=True, blank=True)
    upper_value = models.FloatField(null=True, blank=True)
    min_rank = models.IntegerField(null=True, blank=True)
    max_rank = models.IntegerField(null=True, blank=True)
    min_factor = models.IntegerField(null=True, blank=True)
    max_factor = models.IntegerField(null=True, blank=True)
    display_message = models.CharField(max_length=255, null=True, blank=True)
    created_by = models.IntegerField(null=True, blank=True)
    created = models.DateTimeField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)
    updated = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "rp_variation_factor"
        verbose_name = "Variation Factor"
        verbose_name_plural = "Variation Factors"


class CnextRpVariationFactor(models.Model):
    product_id = models.IntegerField(null=True, blank=True)
    product_type = models.IntegerField(null=True, blank=True)
    result_flow_type = models.IntegerField(null=True, blank=True)
    lower_val = models.IntegerField(null=True, blank=True)
    upper_val = models.IntegerField(null=True, blank=True)
    min_factor = models.FloatField(null=True, blank=True)
    max_factor = models.FloatField(null=True, blank=True)
    preset_type = models.IntegerField(null=True, blank=True)
    status = models.BooleanField(default=True)
    created = models.DateTimeField(null=True, blank=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated = models.DateTimeField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "cnext_rp_variation_factor"
        verbose_name = "Cnext RP Variation Factor"
        verbose_name_plural = "Cnext RP Variation Factors"

class CnextRpSession(models.Model):
    product_id = models.IntegerField(null=True, blank=True)
    product_type = models.IntegerField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    session_date = models.DateTimeField(null=True, blank=True)
    session_shift = models.IntegerField(null=True, blank=True)
    difficulty = models.IntegerField(null=True, blank=True)
    status = models.BooleanField(default=True)
    created = models.DateTimeField(null=True, blank=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated = models.DateTimeField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "cnext_rp_session"
        verbose_name = "Cnext RP Session"
        verbose_name_plural = "Cnext RP Sessions"


class CPProductCampaign(models.Model):
    type = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    alias = models.CharField(max_length=255)
    # description = FroalaField(max_length=10000000, null=True, blank=True,
    #                        options={'toolbarButtons': ['bold', 'insertTable', 'formatUL', 'insertLink', 'html', 'insertImage', 'insertVideo'],
    #                                 'quickInsertButtons': ['table', 'ul'], 'charCounterMax': 10000000})
    # aakash_input_desc = FroalaField(max_length=10000000, null=True, blank=True,
    #                          options={'toolbarButtons': ['bold', 'insertTable', 'formatUL', 'insertLink', 'html', 'insertImage', 'insertVideo'],
    #                                   'quickInsertButtons': ['table', 'ul'], 'charCounterMax': 10000000})
    # input_desc = FroalaField(max_length=10000000, null=True, blank=True,
    #                        options={'toolbarButtons': ['bold', 'insertTable', 'formatUL', 'insertLink', 'html', 'insertImage', 'insertVideo'],
    #                                 'quickInsertButtons': ['table', 'ul'], 'charCounterMax': 10000000})
    listing_desc = models.CharField(max_length=500)
    # icon = VersatileImageField('Images', upload_to='products/', blank=True, null=True)
    # image = VersatileImageField('Images2', upload_to='products/', blank=True, null=True)
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
    # seo_desc = FroalaField(max_length=10000000, null=True, blank=True,
                                    # options={
                                    #     'toolbarButtons': ['bold', 'insertTable', 'formatUL', 'insertLink', 'html', 'insertImage', 'insertVideo'],
                                    #     'quickInsertButtons': ['table', 'ul'], 'charCounterMax': 10000000})
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
    one_step_login = models.IntegerField(default=0)
    gst_include = models.IntegerField(default=0, null=False, blank=True)
    almanac_offer_price = models.IntegerField(default=0, null=False, blank=True)
    free_on_app = models.IntegerField(default=0, null=False, blank=True)
    #new fields are added below
    display_preference = models.IntegerField(null=True, blank=True)
    gif = models.CharField(max_length=255, null=True, blank=True)
    video = models.CharField(max_length=255, null=True, blank=True)
    secondary_image = models.CharField(max_length=255, null=True, blank=True)
    exam = models.IntegerField(null=True, blank=True)
    tool_system_name = models.CharField(max_length=255, null=True, blank=True)
    usage_count_matrix = models.CharField(max_length=255, null=True, blank=True)
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
    promotion_banner_web = models.CharField(max_length=255, null=True, blank=True)
    promotion_banner_wap = models.CharField(max_length=255, null=True, blank=True)
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