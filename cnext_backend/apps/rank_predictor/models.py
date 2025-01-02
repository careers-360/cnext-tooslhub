from django.db import models
from django.utils import timezone
def upload_to(instance, filename):
    return 'tools/images/{filename}'.format(filename=filename)

def upload_sheet(instance, filename):
    year = instance.year if instance.year else "unknown_year"
    product_id = instance.product_id if instance.product_id else "unknown_product"
    return f'tools/merit_sheet/product_id_{product_id}/{year}/{filename}'

class RpMeritSheet(models.Model):
    product_id = models.IntegerField(null=True, blank=True)
    product_type = models.IntegerField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    file_name = models.FileField(upload_to = upload_sheet,null=True, blank=True)
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

class TempRpMeritSheet(models.Model):
    product_id = models.IntegerField(null=True, blank=True)
    product_type = models.IntegerField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    file_name = models.FileField(upload_to = upload_sheet,null=True, blank=True)
    to_graph = models.BooleanField(default=False)
    status = models.BooleanField(default=True)
    created = models.DateTimeField(null=True, blank=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated = models.DateTimeField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "temp_cnext_rp_merit_sheet"
        verbose_name = "temp_cnext_rp_merit_sheet"
        verbose_name_plural = "Temp Merit Sheets"


class RpSmartRegistration(models.Model):
    product_id = models.IntegerField(null=True, blank=True)
    product_type = models.IntegerField(null=True, blank=True)
    field = models.IntegerField(null=True, blank=True)
    peak_season = models.BooleanField(default=False)
    non_peak_season = models.BooleanField(default=False)
    status = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)
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


class RpMeanSd(models.Model):
    product_id = models.IntegerField(null=True, blank=True)
    product_type = models.IntegerField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    # input_flow_type = models.IntegerField(null=True, blank=True)
    input_flow_type = models.ForeignKey(RpInputFlowMaster, on_delete=models.DO_NOTHING, db_column="input_flow_type", null=True, blank=True)
    sheet_mean = models.FloatField(null=True, blank=True)
    sheet_sd = models.FloatField(null=True, blank=True)
    admin_mean = models.FloatField(null=True, blank=True)
    admin_sd = models.FloatField(null=True, blank=True)
    status = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)
    updated_by = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "cnext_rp_mean_sd"
        verbose_name = "Mean and Standard Deviation"
        verbose_name_plural = "Means and Standard Deviations"

class TempRpMeanSd(models.Model):
    product_id = models.IntegerField(null=True, blank=True)
    product_type = models.IntegerField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    # input_flow_type = models.IntegerField(null=True, blank=True)
    input_flow_type = models.ForeignKey(RpInputFlowMaster, on_delete=models.DO_NOTHING, db_column="input_flow_type", null=True, blank=True)
    sheet_mean = models.FloatField(null=True, blank=True)
    sheet_sd = models.FloatField(null=True, blank=True)
    admin_mean = models.FloatField(null=True, blank=True)
    admin_sd = models.FloatField(null=True, blank=True)
    status = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)
    updated_by = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "temp_cnext_rp_mean_sd"
        verbose_name = "Temp Mean and Standard Deviation"
        verbose_name_plural = "Temp Means and Standard Deviations"



class TempRpMeritList(models.Model):
    product_id = models.IntegerField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    caste = models.IntegerField(null=True, blank=True)
    disability = models.IntegerField(null=True, blank=True)
    slot = models.IntegerField(null=True, blank=True)
    difficulty_level = models.IntegerField(null=True, blank=True)
    input_flow_type = models.IntegerField(null=True, blank=True)
    input_value = models.FloatField(null=True, blank=True)
    z_score = models.DecimalField(max_digits=15, decimal_places=10,null=True, blank=True)
    result_flow_type = models.IntegerField(null=True, blank=True)
    result_value = models.FloatField(null=True, blank=True)
    status = models.BooleanField(default=True)
    created = models.DateTimeField(null=True, blank=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated = models.DateTimeField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "temp_cnext_rp_merit_list"
        verbose_name = "Temp Merit List"
        verbose_name_plural = "Temp Merit Lists"

class RpMeritList(models.Model):
    product_id = models.IntegerField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    caste = models.IntegerField(null=True, blank=True)
    disability = models.IntegerField(null=True, blank=True)
    slot = models.IntegerField(null=True, blank=True)
    difficulty_level = models.IntegerField(null=True, blank=True)
    input_flow_type = models.IntegerField(null=True, blank=True)
    input_value = models.FloatField(null=True, blank=True)
    z_score = models.DecimalField(max_digits=15, decimal_places=10,null=True, blank=True)
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
    content = models.TextField(null=True, blank=True)
    image_web = models.ImageField(upload_to = upload_to, blank=True, null=True)
    image_wap = models.ImageField(upload_to = upload_to, blank=True, null=True)
    status = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)
    updated_by = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "cnext_rp_content_section" #TODO change the table and model name
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
    list_option_data = models.TextField(null=True, blank=True)
    mandatory = models.BooleanField(default=False)
    status = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)
    updated_by = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "cnext_rp_form_field"
        verbose_name = "Form Field"
        verbose_name_plural = "Form Fields"

#not used yet
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

    PRESET_TYPE_ENUM = (
        (1, "Excellent"), 
        (2, "Good"), 
        (3, "Bad"), 
        (4, "Very Bad")
    )

    product_id = models.IntegerField(null=True, blank=True)
    product_type = models.IntegerField(null=True, blank=True)
    result_flow_type = models.ForeignKey(RpResultFlowMaster, db_column="result_flow_type", on_delete=models.DO_NOTHING, default=None)
    lower_val = models.IntegerField(null=True, blank=True)
    upper_val = models.IntegerField(null=True, blank=True)
    min_factor = models.FloatField(null=True, blank=True)
    max_factor = models.FloatField(null=True, blank=True)
    preset_type = models.IntegerField(choices=PRESET_TYPE_ENUM, null=True, blank=True)
    status = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)
    updated_by = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "cnext_rp_variation_factor"
        verbose_name = "Cnext RP Variation Factor"
        verbose_name_plural = "Cnext RP Variation Factors"

class CnextRpSession(models.Model):

    DIFFICULTY_ENUM = (
        (1, 'Easy'),
        (2, 'Moderately Easy'),
        (3, 'Moderate'),
        (4, 'Moderately Difficult'),
        (5, 'Difficult'),
    )

    SHIFT_ENUM = (
        (1, 'Shift1'),
        (2, 'Shift2')
    )
    
    product_id = models.IntegerField(null=True, blank=True)
    product_type = models.IntegerField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    session_date = models.DateTimeField(null=True, blank=True)
    session_shift = models.IntegerField(choices=SHIFT_ENUM, null=True, blank=True)
    difficulty = models.IntegerField(choices=DIFFICULTY_ENUM, null=True, blank=True)
    status = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)
    updated_by = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "cnext_rp_session"
        verbose_name = "Cnext RP Session"
        verbose_name_plural = "Cnext RP Sessions"



class RPStudentAppeared(models.Model):
    product_id =  models.IntegerField(null=True, blank=True)
    product_type = models.IntegerField()
    year = models.IntegerField()
    student_type = models.IntegerField(null=False, blank=False)
    category = models.IntegerField()
    disability = models.IntegerField()
    min_student = models.IntegerField()
    max_student = models.IntegerField()
    status = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(default=timezone.now)
    updated_by =  models.IntegerField(null=False, blank=False)
    created_by =  models.IntegerField(null=False, blank=False)

    class Meta:
        db_table = "cnext_rp_student_appeared"
        verbose_name = "rp_student_appeared"
        verbose_name_plural = "rp_student_appeared"

    def __str__(self):
        return f"Student Appeared {self.id} - {self.year}"


class CnextRpCreateInputForm(models.Model):
    product_id = models.IntegerField(null=True, blank=True)
    input_process_type = models.IntegerField(null=True, blank=True)
    process_type_toggle_label = models.CharField(max_length=255, null=True, blank=True)
    submit_cta_name = models.CharField(max_length=255, null=True, blank=True)
    created = models.DateTimeField(null=True, blank=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated = models.DateTimeField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'cnext_rp_create_input_form'
        verbose_name = 'Cnext RP Create Input Form'
        verbose_name_plural = 'Cnext RP Create Input Forms'
        ordering = ['-created']

    def __str__(self):
        return f"Input Form {self.id}"


