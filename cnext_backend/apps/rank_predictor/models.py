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


