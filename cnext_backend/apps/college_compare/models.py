
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import time
from django.db.models import F, Case, When, Value, IntegerField, CharField, ExpressionWrapper,DecimalField,Sum,Q
from django.db.models.functions import Coalesce,Cast,Concat,RowNumber,NullIf
from decimal import Decimal
from django.db.models.functions import Coalesce
from django.core.cache import cache
from hashlib import md5
from functools import reduce
import operator


import locale
from django.db import connection
from django.core.cache import cache

# Set locale for Indian currency formatting
locale.setlocale(locale.LC_ALL, 'en_IN.UTF-8')

def format_fee(value):
    """
    Format the fee value to Indian currency format with ₹ symbol or return 'NA' for zero/invalid values.
    """
    try:
        if int(value) == 0:
            return "NA"
        return f"₹ {locale.format_string('%d', int(value), grouping=True)}"
    except (ValueError, TypeError):
        return "NA"






class ApprovalsAccrediations(models.Model):
    name = models.CharField(max_length=255, db_column='name')
    short_name = models.CharField(max_length=50, db_column='short_name')
    status = models.BooleanField(default=True, db_column='status')

    class Meta:
        db_table = 'approvals_accrediations'
        verbose_name_plural = 'Approvals and Accrediations'
        indexes = [
            models.Index(fields=['short_name']),
        ]



class CollegeAccrediationApproval(models.Model):
    TYPE_CHOICES = [
        ('college_approvals', 'College Approvals'),
        ('college_accrediation', 'College Accrediation')
    ]
    
    college = models.ForeignKey('College', on_delete=models.CASCADE, db_index=True)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    value = models.ForeignKey('ApprovalsAccrediations', on_delete=models.CASCADE,db_column='value')
    
    class Meta:
        db_table = 'college_accrediation_approvals'
        indexes = [
            models.Index(fields=['college', 'type']),
            models.Index(fields=['value']),
        ]


class State(models.Model):
    name = models.CharField(max_length=255)
    status = models.BooleanField(default=True)

    class Meta:
        db_table = 'states'
        indexes = [
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.name or "State Name Not Available"


class Location(models.Model):
    loc_string = models.TextField(null=True, blank=True)
    country_id = models.IntegerField(default=1)
    state_id = models.ForeignKey(
        'State',
        on_delete=models.SET_NULL,
        related_name='locations',
        db_column='state_id',
        null=True,
        blank=True
    )
    city_id= models.IntegerField(null=True, blank=True)
    status = models.BooleanField(default=True)

    class Meta:
        db_table = 'location'
        indexes = [
            models.Index(fields=['country_id', 'state_id', 'status']),
        ]

    def __str__(self):
        return self.loc_string or "Location Not Available"

    @staticmethod
    def get_active_cities_in_country():
        return list(
            State.objects.filter(
                locations__country_id=1,
            ).order_by('name').values_list('name', flat=True).distinct()
        )

class Domain(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    old_domain_name = models.CharField(max_length=200, null=True, blank=True, db_index=True)
    is_stream = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = 'domain'
        indexes = [
            models.Index(fields=['is_stream', 'old_domain_name','name']),
        ]
        app_label = 'college_compare'

        managed = False



class College(models.Model):
    OWNERSHIP_CHOICES = [
        (1, 'Government'),
        (2, 'Private'),
        (3, 'Community'),
        (4, 'Career'),
        (5, 'Global Partnership')
    ]

    INSTITUTE_TYPE_CHOICES = [
        (1, 'Central University'),
        (2, 'State University'),
        (3, 'Deemed to be University'),
        (4, 'Institute of National Importance'),
        (5, 'Institute of Eminence'),
    ]

    ENTITY_TYPE_CHOICES = [
        (1, 'University'),
        (2, 'College'),
        (3, 'Hospital'),
        (4, 'Instructor'),
        (5, 'Organization'),
    ]

    name = models.CharField(max_length=255, db_index=True)
    short_name = models.CharField(max_length=50, blank=True,default='NA')
    published = models.CharField(max_length=20, default='published', db_index=True)
    status = models.BooleanField(default=True)
    ownership = models.IntegerField(choices=OWNERSHIP_CHOICES)
    institute_type_1 = models.IntegerField(choices=INSTITUTE_TYPE_CHOICES, null=True, blank=True)
    institute_type_2 = models.IntegerField(choices=INSTITUTE_TYPE_CHOICES, null=True, blank=True)
    type_of_entity = models.IntegerField(choices=ENTITY_TYPE_CHOICES, null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)
    campus_size = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    year_of_establishment = models.IntegerField(null=True, blank=True)
    popular_stream = models.IntegerField(null=True, blank=True)
    domains = models.ManyToManyField(Domain, through='CollegeDomain', related_name='colleges')
    entity_reference = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sub_institutes',
        db_column='entity_reference'
    )
    country_id = models.IntegerField(default=1, db_index=True)
    total_faculty = models.IntegerField(null=True, blank=True)
    associate_hospital=models.CharField(null=True,max_length=100,blank=True)
    number_of_bed=models.CharField(null=True,max_length=10,blank=True)



    class Meta:
        db_table = 'colleges'
        verbose_name_plural = 'Colleges'
        ordering = ['name']
        indexes = [
            models.Index(fields=['published', 'name']),
            models.Index(fields=['country_id']),
            models.Index(fields=['popular_stream']),
            models.Index(fields=['published', 'status', 'country_id']),
        ]

    def __str__(self):
        return self.name

    def ownership_display(self):
        return dict(self.OWNERSHIP_CHOICES).get(self.ownership, '-')

   

    @staticmethod
    def type_of_institute(institute_type_1, institute_type_2):
        type_mapping = {
            1: 'Central University',
            2: 'State University',
            3: 'Deemed to be University',
            4: 'Institute of National Importance',
            5: 'Institute of Eminence',
        }

        # Handle individual types
        type1_label = type_mapping.get(institute_type_1, None)
        type2_label = type_mapping.get(institute_type_2, None)

        if institute_type_1 and institute_type_2:
            # Create a combined label
            combined_types = ', '.join(sorted(filter(None, [type1_label, type2_label])))
            return combined_types if combined_types else '-'
        
        # Handle single institute type
        if type1_label:
            return type1_label
        if type2_label:
            return type2_label

        return '-'

    

    def parent_institute(self):
        if self.entity_reference:
            return self.entity_reference.short_name or 'NA'
        return 'NA'

    def campus_size_in_acres(self):
        if self.campus_size:
            return f"{int(self.campus_size):,} Acres"
        return 'NA'
    

class CollegeFacility(models.Model):
    FACILITY_CHOICES = [
        (1, 'Boys Hostel'),
        (2, 'Girls Hostel'),
        (3, 'Classrooms'),
        (4, 'Wifi'),
        (5, 'Library'),
        (6, 'Laboratories'),
        (7, 'Moot Court'),
        (8, 'Auditorium'),
        (9, 'Cafeteria'),
        (10, 'Medical/Hospital'),
        (11, 'Convenience Store'),
        (12, 'I.T Infrastructure'),
        (13, 'Swimming Pool'),
        (14, 'Gym'),
        (15, 'Sports'),
        (16, 'Alumni Associations'),
        (17, 'Banks/ATMs'),
        (18, 'Guest Room/Waiting Room'),
        (19, 'Parking Facility'),
        (20, 'Transport Facility'),
        (21, 'Accommodation'),
        (22, 'Club'),
        (23, 'Mess'),
        (24, 'Workshops'),
        (25, 'Extra Curricular Activities'),
        (26, 'Training and Placement Cell'),
        (27, 'Physical Challenged Student'),
        (28, 'Smart Classrooms')
    ]
    
    college = models.ForeignKey('College', on_delete=models.CASCADE, db_index=True)
    facility = models.IntegerField(choices=FACILITY_CHOICES)

    class Meta:
        db_table = 'college_facilities'
        indexes = [
            models.Index(fields=['college', 'facility']),
        ]





class CollegePlacement(models.Model):
    college = models.ForeignKey('College', on_delete=models.CASCADE, db_index=True)
    year = models.IntegerField(db_index=True)
    intake_year = models.IntegerField(db_index=True)
    levels = models.IntegerField(db_index=True)
    total_students = models.IntegerField(null=True, blank=True)
    total_offers = models.IntegerField(null=True, blank=True)
    male_students = models.IntegerField(null=True, blank=True)
    female_students = models.IntegerField(null=True, blank=True)
    outside_state = models.IntegerField(null=True, blank=True)
    outside_country = models.IntegerField(null=True, blank=True)
    no_placed = models.IntegerField(null=True, blank=True)
    max_salary_dom = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_salary_inter = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    inter_offers = models.IntegerField(null=True, blank=True)
    avg_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    median_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    student_count_hs = models.IntegerField(null=True, blank=True)
    entity_type = models.IntegerField(null=True, blank=True)
    programme = models.CharField(max_length=255, null=True, blank=True)
    graduating_students = models.IntegerField(null=True, blank=True) 
    published = models.CharField(max_length=20, default='published')
    reimbursement_gov = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reimbursement_institution = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reimbursement_private_bodies = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stream = models.ForeignKey('Domain', on_delete=models.CASCADE, db_index=True, db_column="stream_id", null=True, blank=True)

    class Meta:
        db_table = 'college_placements'
        indexes = [
            models.Index(fields=['college', 'year', 'intake_year', 'levels']),
            models.Index(fields=['published']),
            models.Index(fields=['stream']),
        ]




class CollegePlacementCompany(models.Model):
    collegeplacement = models.ForeignKey(
        'CollegePlacement', on_delete=models.CASCADE, db_index=True
    )
    company = models.ForeignKey(
        'Company', on_delete=models.CASCADE, db_index=True
    )

    class Meta:
        db_table = 'college_placements_companies'
        indexes = [
            models.Index(fields=['collegeplacement', 'company']),
        ]

class Company(models.Model):
    name = models.CharField(max_length=255)
    popular_name = models.CharField(max_length=255, null=True, blank=True)
    logo = models.CharField(max_length=100, null=True, blank=True)
    remark = models.TextField(null=True, blank=True)
    published = models.CharField(max_length=255, default='draft')

    class Meta:
        db_table = 'companies'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['popular_name']),
            models.Index(fields=['published']),
        ]


class Degree(models.Model):
    name = models.CharField(max_length=255, unique=True)
    published = models.CharField(max_length=20, default='published')

    class Meta:
        db_table = 'degrees'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['published']),
        ]

    def __str__(self):
        return self.name


class Branch(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'branches'
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name




  

    # @staticmethod
    # def get_total_tuition_fee_by_course(course_id, session):
    #     """
    #     Args:
    #         course_id (int): The ID of the course
    #         session (int): The academic session year
        
    #     Returns:
    #         dict: Dictionary containing formatted total fees for each category
    #     """
    #     cache_key = f"tuition_____fees___{course_id}_{session}"
    #     cached_data = cache.get(cache_key)
    #     if cached_data:
    #         return cached_data

    #     total_fees = {
    #         'total_tuition_fee_general': Decimal('0'),
    #         'total_tuition_fee_sc': Decimal('0'),
    #         'total_tuition_fee_st': Decimal('0'),
    #         'total_tuition_fee_obc': Decimal('0'),
    #     }

    #     try:
    #         course = Course.objects.get(id=course_id)
    #         if not course.course_duration:
    #             return {key: format_fee(value) for key, value in total_fees.items()}
       
    #         years = Decimal(str(course.course_duration)) / Decimal('6')
         
    #         yearly_fee = CollegeCourseFee.objects.filter(
    #             course_fee_duration__college_course_id=course_id,
    #             course_fee_duration__college_course__sessions__session=session,
    #             fee_category='institute_fee',
    #             fee_types__fee_type=36,
    #         ).first()
            
    #         if yearly_fee:
    #             print(years,"------")
               
    #             for category in ['general', 'sc', 'st', 'obc']:
    #                 fee_value = getattr(yearly_fee, category)
    #                 if fee_value is not None:
    #                     total_fees[f'total_tuition_fee_{category}'] = \
    #                         Decimal(str(fee_value)) * years

    #     except Course.DoesNotExist:
    #         return {key: format_fee(value) for key, value in total_fees.items()}

    #     formatted_fees = {key: format_fee(value) for key, value in total_fees.items()}

    #     if any(total_fees.values()):
    #         cache.set(cache_key, formatted_fees, 3600 * 24)  

    #     return formatted_fees

class CollegeDomain(models.Model):
    college = models.ForeignKey('College', on_delete=models.CASCADE, related_name='collegedomain', db_index=True)
    college_course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='collegedomain_course', db_index=True)
    domain = models.ForeignKey('Domain', on_delete=models.CASCADE, db_index=True)
    status = models.BooleanField(default=True, verbose_name=("Status"))


    class Meta:
        db_table = 'colleges_course_domains'
        unique_together = ['college', 'domain', 'college_course']
        indexes = [
            models.Index(fields=['college', 'domain', 'college_course']),
        ]

    def __str__(self):
        return f"{self.college.name} - {self.domain.name} - {self.college_course}"





class CollegeReviews(models.Model):
    college = models.ForeignKey(
        'College', 
        on_delete=models.CASCADE, 
        related_name='reviews',
        db_index=True
    )
    college_course = models.ForeignKey(
        'Course', 
        on_delete=models.CASCADE, 
        related_name='reviews',
        null=True, 
        blank=True, 
        db_index=True
    )
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='reviews',
        db_column='uid'
    )
    
    # Rating fields (0-100 scale)
    overall_rating = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        db_index=True
    )
    infra_rating = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    college_life_rating = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    academics_rating = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    affordability_rating = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    placement_rating = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    faculty_rating = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Review content
    title = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    campus_life = models.TextField(null=True, blank=True)
    college_infra = models.TextField(null=True, blank=True) 
    academics = models.TextField(null=True, blank=True)
    placements = models.TextField(null=True, blank=True)
    value_for_money = models.TextField(null=True, blank=True)
    
    # Metadata
    graduation_year = models.DateField(db_index=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'college_reviews'
        indexes = [
            models.Index(fields=['college', 'graduation_year', 'status']),
            models.Index(fields=['college', 'created']),
            models.Index(fields=['user', 'college']),
        ]

    def __str__(self):
        return f"Review for {self.college.name} by {self.user.display_name}"

    @staticmethod
    def get_rating_display(rating_value):
        """Convert 100-point scale to 5-point scale"""
        return round(rating_value / 20, 1)

    # Rating display properties
    @property
    def overall_rating_display(self):
        return self.get_rating_display(self.overall_rating)

    @property
    def infra_rating_display(self):
        return self.get_rating_display(self.infra_rating)
    
    @property
    def college_life_rating_display(self):
        return self.get_rating_display(self.college_life_rating)
    
    @property
    def academics_rating_display(self):
        return self.get_rating_display(self.academics_rating)
    
    @property
    def affordability_rating_display(self):
        return self.get_rating_display(self.affordability_rating)
    
    @property
    def placement_rating_display(self):
        return self.get_rating_display(self.placement_rating)
    
    @property
    def faculty_rating_display(self):
        return self.get_rating_display(self.faculty_rating)


class CollegeData(models.Model):
    college = models.OneToOneField(
        College, on_delete=models.CASCADE, db_column='college_id', related_name='data'
    )
    courses = models.TextField(null=True, blank=True)
    placements = models.TextField(null=True, blank=True)
    adm_process = models.TextField(null=True, blank=True)
    review = models.TextField(null=True, blank=True)
    total_review = models.IntegerField(null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    cut_off = models.IntegerField(null=True, blank=True)
    qna_answered = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'colleges_data'
        indexes = [
            models.Index(fields=['college']),
        ]



class CollegeCompareData(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.IntegerField(db_index=True)
    college_1 = models.ForeignKey(
        'College', on_delete=models.CASCADE, related_name='comparisons_1', db_column='college_1', db_index=True
    )
    course_1 = models.ForeignKey(
        'Course', on_delete=models.CASCADE, related_name='course_comparisons_1', db_column='course_1', db_index=True
    )
    college_2 = models.ForeignKey(
        'College', on_delete=models.CASCADE, related_name='comparisons_2', db_column='college_2', db_index=True
    )
    course_2 = models.ForeignKey(
        'Course', on_delete=models.CASCADE, related_name='course_comparisons_2', db_column='course_2', db_index=True
    )
    college_3 = models.ForeignKey(
        'College', on_delete=models.CASCADE, related_name='comparisons_3', db_column='college_3', null=True, blank=True, db_index=True
    )
    course_3 = models.ForeignKey(
        'Course', on_delete=models.CASCADE, related_name='course_comparisons_3', db_column='course_3', null=True, blank=True, db_index=True
    )
    college_4 = models.ForeignKey(
        'College', on_delete=models.CASCADE, related_name='comparisons_4', db_column='college_4', null=True, blank=True, db_index=True
    )
    course_4 = models.ForeignKey(
        'Course', on_delete=models.CASCADE, related_name='course_comparisons_4', db_column='course_4', null=True, blank=True, db_index=True
    )
    device = models.CharField(max_length=32)

    created = models.BigIntegerField(default=lambda: int(time.time()), editable=False)  
    updated = models.BigIntegerField(default=0)
    count = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = int(time.time())
        self.updated = int(time.time()) 
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'college_compare_data'
        indexes = [
          
            models.Index(fields=[
                'uid', 'college_1', 'college_2', 'college_3', 'college_4',
                'course_1', 'course_2', 'course_3', 'course_4'
            ]),
            models.Index(fields=['college_1', 'course_1']),
            models.Index(fields=['college_2', 'course_2']),
            models.Index(fields=['college_3', 'course_3']),
            models.Index(fields=['college_4', 'course_4']),
             models.Index(fields=['college_1', 'college_2', 'college_3', 'college_4']),
            models.Index(fields=['course_1', 'course_2', 'course_3', 'course_4']),
            models.Index(fields=['course_1', 'course_2']),
            models.Index(fields=['course_1', 'course_2', 'college_1', 'college_2']),
            models.Index(fields=['course_1', 'course_2', 'college_1']),
            models.Index(fields=['college_1', 'college_2']),
            models.Index(fields=['college_1']),
            models.Index(fields=['college_2']),
            models.Index(fields=['course_1']),
            models.Index(fields=['course_2']),
                 models.Index(fields=['college_3']),
            models.Index(fields=['college_4']),
      

     
        ]

        unique_together = ['course_1', 'course_2','college_1',"college_2"] 
        verbose_name = 'College Comparison Data'
        verbose_name_plural = 'College Comparison Data'

    def __str__(self):
        return f"Comparison by User {self.uid}: [{self.college_1}, {self.college_2}, {self.college_3}, {self.college_4}]"



class User(models.Model):
    uid = models.IntegerField(unique=True, primary_key=True)
    domain = models.ForeignKey('Domain', on_delete=models.SET_NULL, null=True, related_name='users')
    current_education_level = models.IntegerField(null=True)
    display_name = models.CharField(max_length=255)

    class Meta:
        db_table = 'users'

    def get_education_level_mark(self):
        education_level_map = {
            1: (6, 7, 8, 17),
            2: (14, 15, 16, 18)
        }

        for level, levels in education_level_map.items():
            if self.current_education_level in levels:
                return level
        
        return None



class SocialMediaGallery(models.Model):
    college = models.ForeignKey(
        College, 
        on_delete=models.CASCADE, 
        related_name='social_media_gallery'
    )
    logo = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'social_media_gallary'
        verbose_name_plural = 'Social Media Gallery'






class Ranking(models.Model):
    ranking_authority = models.CharField(max_length=255)
    ranking_stream = models.CharField(max_length=255)
    nirf_stream = models.CharField(max_length=255, blank=True, null=True)
    nirf_entity = models.CharField(max_length=255, blank=True, null=True)
    ranking_entity = models.CharField(max_length=255, blank=True, null=True)
    year = models.IntegerField()  
    status = models.IntegerField(default=1)

    class Meta:
        db_table = 'ranking'


class RankingUploadList(models.Model):
    college = models.ForeignKey(
        'College',
        on_delete=models.CASCADE,
        related_name='ranking_uploads',
        db_index=True,
        db_column="college_id"
    )
    ranking = models.ForeignKey(
        'Ranking',
        on_delete=models.CASCADE,
        related_name='upload_list',
        db_index=True,
        db_column='ranking_id'
    )

    overall_rank = models.IntegerField(null=True, blank=True)
    overall_rating = models.CharField(max_length=50, null=True, blank=True)
    overall_score = models.FloatField(null=True, blank=True)  
    rank_band=models.CharField(null=True,blank=True,max_length=50)

    class Meta:
        db_table = 'ranking_upload_list'
        indexes = [
            models.Index(fields=['college', 'ranking']),
           
        ]

    def __str__(self):
        return f"{self.college.name} - {self.ranking.ranking_authority} ({self.year})"



class RankingParameters(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    score = models.FloatField()
    total = models.IntegerField()
    ranking_upload = models.ForeignKey(
        'RankingUploadList',
        on_delete=models.CASCADE,
        related_name='parameters',
        db_index=True,
        db_column="ranking_upload_id"
    )

    class Meta:
        db_table = 'ranking_parameters'
        indexes = [
            models.Index(fields=['ranking_upload']),
        ]

    def __str__(self):
        return f"{self.name} (Score: {self.score}/{self.total})"

class FeeBifurcation(models.Model):
    college_course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='fees', db_index=True)
    category = models.CharField(max_length=50)  
    total_fees = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'fees_bifurcations'
        indexes = [
            models.Index(fields=['college_course', 'category']),
        ]






class CollegeCourseFee(models.Model):
    course_fee_duration = models.ForeignKey('CourseFeesDuration', on_delete=models.CASCADE, related_name='fees', db_index=True)
    fee_category = models.CharField(max_length=255)
    obc = models.IntegerField(null=True, blank=True)  # OBC Fee
    sc = models.IntegerField(null=True, blank=True)   # SC Fee
    st = models.IntegerField(null=True, blank=True)   # ST Fee
    general = models.IntegerField(null=True, blank=True)  # General Fee
    ls = models.IntegerField()  # LS Fee
    ints = models.IntegerField()  # Ints Fee

    class Meta:
        db_table = 'college_course_fee_data'

    def __str__(self):
        return f"{self.fee_category} for Course Fee Duration {self.course_fee_duration}"
    @staticmethod
    def handle_na_case(value):
        """Helper function to return 'NA' if value is None"""
        return 'NA' if value is None else value
    @staticmethod
    def get_total_tuition_fee_by_course(course_id, session):
        """
        Args:
            course_id (int): The ID of the course
            session (int): The academic session year

        Returns:
            dict: Dictionary containing total fees for each category
        """
        cache_key = f"tuitionfees_{course_id}_{session}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

    
        total_fees = {
            'total_tuition_fee_general': 'NA',
            'total_tuition_fee_sc': 'NA',
            'total_tuition_fee_st': 'NA',
            'total_tuition_fee_obc': 'NA',
        }

        
        sql = """
            SELECT
                SUM(ccfd.general) AS total_general_tuition,
                SUM(ccfd.sc) AS total_sc_tuition,
                SUM(ccfd.st) AS total_st_tuition,
                SUM(ccfd.obc) AS total_obc_tuition
            FROM
                django360.college_course_fee ccf
            JOIN
                django360.college_course_fee_data ccfd ON ccf.id = ccfd.course_fee_duration_id
            JOIN
                django360.college_course_fee_fees_type ccfft ON ccfd.id = ccfft.fee_data_id
            JOIN
                django360.college_course_fee_type ccft ON ccfft.fee_type = ccft.id
            WHERE
                ccf.college_course_id = %s
                AND ccf.session_type = 'year'
                AND ccf.session = %s
                AND ccft.name = 'Tuition Fees'
                AND ccfft.fee_type = 36
        """

     

        with connection.cursor() as cursor:
            cursor.execute(sql, [course_id, session])
            row = cursor.fetchone()

   
        if row:
            total_fees = {
                'total_tuition_fee_general': format_fee(row[0]),
                'total_tuition_fee_sc': format_fee(row[1]),
                'total_tuition_fee_st': format_fee(row[2]),
                'total_tuition_fee_obc': format_fee(row[3]),
            }

   
        cache.set(cache_key, total_fees, 3600 * 24)

        return total_fees
class CollegeCourseFeeType(models.Model):
    fee_data = models.ForeignKey('CollegeCourseFee', on_delete=models.CASCADE, related_name='fee_types')
    fee_type = models.IntegerField()
    updated = models.DateTimeField(auto_now=True)
    updated_by = models.IntegerField()

    class Meta:
        db_table = 'college_course_fee_fees_type'

    def __str__(self):
        return f"Fee Type {self.fee_type} for Fee Data ID {self.fee_data.id}"

class FeeType(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'college_course_fee_type'

    def __str__(self):
        return self.name

class CourseFeesDuration(models.Model):
    type = models.CharField(max_length=255)
    count = models.IntegerField()  # Duration in months or years
    college_course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='fee_durations')

    class Meta:
        db_table = 'course_fees_durations'

    def __str__(self):
        return f"{self.type} - {self.count} months"

class CollegeCourseSession(models.Model):
    college_course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='sessions')
    session = models.IntegerField()  # The session year (e.g. 2024)
    session_type = models.CharField(max_length=255)  # E.g., Semester, Annual
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.IntegerField()
    updated = models.DateTimeField(auto_now=True)
    updated_by = models.IntegerField()

    class Meta:
        db_table = 'college_course_fee'

    def __str__(self):
        return f"Session {self.session} for {self.college_course.course_name} ({self.session_type})"

class CollegeCourseExam(models.Model):
    college_course = models.ForeignKey(
        'Course', 
        on_delete=models.CASCADE, 
        related_name='exams', 
        db_column='collegecourse_id',
        db_index=True
    )
    exam = models.ForeignKey(
        'Exam', 
        on_delete=models.CASCADE, 
        related_name='college_courses', 
        db_column='exam_id',  
        db_index=True
    )

    class Meta:
        db_table = 'colleges_courses_exam'
        indexes = [
            models.Index(fields=['college_course', 'exam']),
        ]


class CourseApprovalAccrediation(models.Model):
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='approvals', db_index=True)
    value = models.ForeignKey('ApprovalsAccrediations', on_delete=models.CASCADE,db_column='value')
    type = models.CharField(max_length=50)  
    class Meta:
        db_table = 'course_approval_accrediations'
        indexes = [
            models.Index(fields=['course', 'type']),
        ]



class Course(models.Model):
    LEVEL_CHOICES = [
        (1, 'Undergraduate'),
        (2, 'Postgraduate')
    ]

    STUDY_MODE_CHOICES = [
        (1, 'online'),
        (2, 'offline')
    ]

    CREDENTIAL_CHOICES = [
        (0, 'Degree'),
        (1, 'Diploma'),
        (2, 'Certificate')
    ]

    course_name = models.CharField(max_length=255)
    college = models.ForeignKey('College', on_delete=models.CASCADE, related_name='courses', db_index=True)
    degree = models.ForeignKey('Degree', on_delete=models.SET_NULL, null=True, blank=True, related_name='course')
    branch = models.ForeignKey('Branch', on_delete=models.CASCADE, null=True, blank=True, related_name='course')
    degree_domain = models.ForeignKey('Domain', on_delete=models.SET_NULL, null=True, blank=True, related_name='courses', db_index=True, db_column="degree_domain")
    level = models.IntegerField(choices=LEVEL_CHOICES)
    status = models.BooleanField(default=True)
    course_duration = models.IntegerField(null=True, blank=True)  # in months
    study_mode = models.IntegerField(choices=STUDY_MODE_CHOICES, null=True, blank=True)
    approved_intake = models.IntegerField(null=True, blank=True)
    admission_procedure = models.TextField(null=True, blank=True)
    eligibility_criteria = models.TextField(null=True, blank=True)
    credential = models.IntegerField(choices=CREDENTIAL_CHOICES, default=0)  # Default to Degree (0)

    class Meta:
        db_table = 'colleges_courses'
        unique_together = ['course_name', 'college', 'level']
        indexes = [
            models.Index(fields=['degree', 'branch', 'college', 'status']),
            models.Index(fields=['degree_domain']),
            models.Index(fields=['degree_domain','level']),
            models.Index(fields=['college']), # For filtering courses by college
            models.Index(fields=['degree']), # For filtering courses by degree
            models.Index(fields=['status']), # For filtering courses by status
            models.Index(fields=['college', 'degree', 'status']), # For total_courses_offered method
  
            
        ]

    def __str__(self):
        return f"{self.course_name} ({self.get_level_display()})"

    def total_courses_offered(self):
        """
        Calculate the total number of courses offered by the college
        for the specific degree.
        """
        return Course.objects.filter(
            college=self.college,
            degree=self.degree,
            status=True
        ).count()
    
    @staticmethod
    def get_cache_key(course_id, session):
        """Generate a unique cache key based on course_id and session"""
        key = f"tuition_fee_{course_id}_{session}"
        return md5(key.encode()).hexdigest()
    

    @staticmethod
    def get_total_tuition_fee_by_course(course_id, session):
        """
        Args:
            course_id (int): The ID of the course
            session (int): The academic session year

        Returns:
            dict: Dictionary containing formatted total fees for each category
        """
        cache_key = f"tuition_fee_{course_id}_{session}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        # Default response structure
        total_fees = {
            'total_tuition_fee_general': 'NA',
            'total_tuition_fee_sc': 'NA',
            'total_tuition_fee_st': 'NA',
            'total_tuition_fee_obc': 'NA',
        }

        # Raw SQL query
        sql = """
            SELECT
                SUM(ccfd.general) AS total_general_tuition,
                SUM(ccfd.sc) AS total_sc_tuition,
                SUM(ccfd.st) AS total_st_tuition,
                SUM(ccfd.obc) AS total_obc_tuition
            FROM
                django360.college_course_fee ccf
            JOIN
                django360.college_course_fee_data ccfd ON ccf.id = ccfd.course_fee_duration_id
            JOIN
                django360.college_course_fee_fees_type ccfft ON ccfd.id = ccfft.fee_data_id
            JOIN
                django360.college_course_fee_type ccft ON ccfft.fee_type = ccft.id
            WHERE
                ccf.college_course_id = %s
                AND ccf.session_type = 'year'
                AND ccf.session = %s
                AND ccft.name = 'Tuition Fees'
                AND ccfft.fee_type = 36
        """

        # Execute the query
        with connection.cursor() as cursor:
            cursor.execute(sql, [course_id, session])
            row = cursor.fetchone()

        # Update response structure with actual values if query returned data
        if row:
            total_fees = {
                'total_tuition_fee_general': format_fee(row[0]),
                'total_tuition_fee_sc': format_fee(row[1]),
                'total_tuition_fee_st': format_fee(row[2]),
                'total_tuition_fee_obc': format_fee(row[3]),
            }

        # Cache the result
        cache.set(cache_key, total_fees, 3600 * 24)

        return total_fees
    

class Exam(models.Model):
    exam_name = models.CharField(max_length=255)
    exam_short_name = models.CharField(max_length=50, null=True, blank=True)
    super_parent_id = models.IntegerField(null=True, blank=True)  
    instance_year = models.IntegerField()  
    status = models.CharField(max_length=20, db_index=True)
    state_of_exam_id = models.IntegerField(null=True, blank=True) 
    preferred_education_level_id = models.IntegerField(null=True, blank=True, db_index=True)
    parent_exam = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='child_exams'
    )

    class Meta:
        db_table = 'exams'
        indexes = [
            models.Index(fields=['exam_name', 'exam_short_name'], name='exam_name_short_name_idx'),
            models.Index(fields=['instance_year'], name='exam_instance_year_idx'),
            models.Index(fields=['status'], name='exam_status_idx'),
            models.Index(fields=['super_parent_id'], name='exam_super_parent_id_idx'),
            models.Index(fields=['state_of_exam_id'], name='exam_state_of_exam_id_idx'),
            models.Index(fields=['preferred_education_level_id'], name='preferred_education_level_idx'),
            models.Index(fields=['parent_exam'], name='exam_parent_exam_idx'), # For filtering by parent exam
   
        ]
        app_label = 'college_compare'
        managed = False

    def __str__(self):
        return self.get_exam_display_name()

    def get_exam_display_name(self):
        if self.exam_short_name:
            return self.exam_short_name
        
        if self.parent_exam:
            return f"{self.parent_exam.exam_short_name or self.parent_exam.exam_name} ({self.exam_name})"
        return self.exam_name

     


class CutoffData(models.Model):
    college = models.ForeignKey(
        'College', 
        on_delete=models.CASCADE, 
        db_index=True, 
        related_name='cutoff_data'
    )

    college_course = models.ForeignKey(
        'Course', 
        on_delete=models.CASCADE, 
        db_index=True, 
        related_name='cutoff_records'  # Changed from cutoff_data to cutoff_records
    )
  
    round = models.IntegerField(db_index=True)  
    round_wise_opening_cutoff = models.FloatField(null=True, blank=True)  
    round_wise_closing_cutoff = models.FloatField(null=True, blank=True)  
    category_of_admission = models.ForeignKey(
        'AdmissionCategory', 
        on_delete=models.SET_DEFAULT, 
        default=1, 
        db_index=True
    )
    caste_id = models.IntegerField(null=True, blank=True, db_index=True) 
    year = models.IntegerField(db_index=True)
    exam_sub_exam = models.ForeignKey(
        'Exam', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        db_column='exam_sub_exam_id', 
        db_index=True,
        related_name="cutoff_data"
    )
    counselling_id = models.IntegerField(null=True, blank=True, db_index=True)  #
    branch_id = models.IntegerField(db_index=True)
    final_cutoff = models.FloatField(null=True, blank=True)  
    gender_id=models.IntegerField(null=True,blank=True,db_index=True)

    class Meta:
        db_table = 'cp_cutoff_final'
        indexes = [
            models.Index(fields=['college', 'college_course']),
            models.Index(fields=['category_of_admission']),
            models.Index(fields=['round']),
            models.Index(fields=['year']),
            models.Index(fields=['exam_sub_exam']),
            models.Index(fields=['branch_id']),
            models.Index(fields=['caste_id']),
            models.Index(fields=['counselling_id']),  # Added index for performance in query joins
             models.Index(fields=['college_course', 'year', 'exam_sub_exam', 'counselling_id', 'caste_id', 'category_of_admission']), # For fetch_cutoff_data
            models.Index(fields=['college_course', 'year']), # For fetching data by college course and year
            models.Index(fields=['college', 'year']), # For fetching data by college and year
            models.Index(fields=['college_course', 'exam_sub_exam', 'counselling_id']), # For filtering cutoff data
            models.Index(fields=['college_course', 'caste_id', 'category_of_admission']), # For filtering cutoff data
            models.Index(fields=['college_course', 'exam_sub_exam', 'counselling_id', 'caste_id', 'category_of_admission']), # For filtering cutoff data
     # For filtering cutoff data
            models.Index(fields=['college_course','exam_sub_exam','counselling_id','caste_id']), # For filtering cutoff data
    # For filtering cutoff data
 
        ]

    def __str__(self):
        return (
            f"Cutoff Data for {self.college.name} - {self.college_course.course_name} "
            f"(Round: {self.round}, Year: {self.year})"
        )


class CpProductCampaign(models.Model):
    STATUS_CHOICES = [
        ('published', 'Published'),
        ('draft', 'Draft'),
        ('archived', 'Archived'),
    ]

    name = models.CharField(max_length=255)
    published = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cp_product_campaign'
        indexes = [
            models.Index(fields=['published']),
        ]
        app_label = 'college_compare'

        managed = False

    def __str__(self):
        return f"{self.name} ({self.get_published_display()})"
    

    
class CpProductCampaignItems(models.Model):
    product = models.ForeignKey(
        CpProductCampaign,
        on_delete=models.CASCADE,
        related_name='campaign_items'
    )
    exam_id = models.IntegerField(db_index=True)  
    counselling_id = models.IntegerField(db_index=True)  
    class Meta:
        db_table = 'cp_product_campaign_items'
        indexes = [
            models.Index(fields=['exam_id']),
            models.Index(fields=['counselling_id']),
            models.Index(fields=['product']), # For filtering by product
            models.Index(fields=['product', 'exam_id', 'counselling_id']), # For filtering by product, exam and counseling
 
        ]

    def __str__(self):
        return f"Item for {self.product.name} (Exam ID: {self.exam_id}, Counseling ID: {self.counselling_id})"
    
    



class AdmissionCategory(models.Model):
    description = models.CharField(max_length=255)

    class Meta:
        db_table = 'cp_admission_category'

    def __str__(self):
        return self.description



class CollegeCourseComparisonFeedback(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.IntegerField(db_index=True)
    voted_college = models.ForeignKey(
        'College', on_delete=models.CASCADE, related_name='voted_comparisons',db_column='voted_college'
    )
    voted_course = models.ForeignKey(
        'Course', on_delete=models.CASCADE, related_name='voted_course_comparisons',db_column='voted_course'
    )
    college_1 = models.ForeignKey(
        'College', on_delete=models.CASCADE, related_name='comparisons_feedback_1',db_column='college_1'
    )
    course_1 = models.ForeignKey(
        'Course', on_delete=models.CASCADE, related_name='course_comparisons_feedback_1',db_column='course_1'
    )
    college_2 = models.ForeignKey(
        'College', on_delete=models.CASCADE, related_name='comparisons_feedback_2',db_column='college_2'
    )
    course_2 = models.ForeignKey(
        'Course', on_delete=models.CASCADE, related_name='course_comparisons_feedback_2',db_column='course_2'
    )
    college_3 = models.ForeignKey(
        'College', on_delete=models.CASCADE, related_name='comparisons_feedback_3',db_column='college_3',
        null=True, blank=True
    )
    course_3 = models.ForeignKey(
        'Course', on_delete=models.CASCADE, related_name='course_comparisons_feedback_3',db_column='course_3',
        null=True, blank=True
    )
    createdAt = models.DateTimeField(auto_now_add=True)
    createdBy = models.CharField(max_length=255, null=True, blank=True)
    updatedAt = models.DateTimeField(auto_now=True)
    updatedBy = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'college_course_comparison_feedback'
        indexes = [
            models.Index(fields=['uid', 'voted_college', 'voted_course', 'createdAt']),
            models.Index(fields=['voted_college', 'voted_course'])
        ]
        verbose_name = 'College Course Comparison Feedback'
        verbose_name_plural = 'College Course Comparison Feedback'

    def __str__(self):
        return f"Feedback by User {self.uid}: Voted [{self.voted_college}, {self.voted_course}]"
 

class UserReportPreferenceMatrix(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.ForeignKey('users.User', on_delete=models.CASCADE, db_index=True,db_column="uid")
    course_1 = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='user_preferences_1', db_index=True,db_column="course_1")
    course_2 = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='user_preferences_2', db_index=True, db_column="course_2")
    course_3 = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='user_preferences_3', db_index=True, null=True, blank=True, db_column="course_3")

    preference_1 = models.CharField(max_length=255, null=True, blank=True)
    preference_2 = models.CharField(max_length=255, null=True, blank=True)
    preference_3 = models.CharField(max_length=255, null=True, blank=True)
    preference_4 = models.CharField(max_length=255, null=True, blank=True)
    preference_5 = models.CharField(max_length=255, null=True, blank=True)


    fees_budget = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        help_text="Budget for course fees (up to 1 lakh)"
    )
    location_states = models.JSONField(
        null=True, 
        blank=True,
        help_text="List of preferred location states"
    )
    exams = models.JSONField(
        null=True, 
        blank=True,
        help_text="List of relevant exams"
    )



    class Meta:
        db_table = 'user_report_preference_matrix'
        indexes = [
            models.Index(fields=['uid']),
            models.Index(fields=['preference_1', 'preference_2', 'preference_3', 'preference_4', 'preference_5']),
            models.Index(fields=['course_1', 'course_2', 'course_3']),
        ]


from django.db import models
from django.core.validators import MinLengthValidator
from django.utils.timezone import now
from django.db import transaction


class UrlMetaPattern(models.Model):
    """
    Defines different types of URL patterns used throughout the application.
    This model serves as a reference table for categorizing and organizing URLs.
    Each pattern can be associated with multiple URL aliases.
    """
    id = models.AutoField(
        primary_key=True,
        help_text="Unique identifier for the URL pattern"
    )
    type = models.CharField(
        max_length=255,
        validators=[MinLengthValidator(1)],
        help_text="Type of URL pattern (e.g., 'compare-colleges', 'profile')",
        db_index=True
    )

    class Meta:
        db_table = 'base_url_meta_pattern'
        verbose_name = 'URL Meta Pattern'
        verbose_name_plural = 'URL Meta Patterns'
        indexes = [
            models.Index(fields=['type'], name='url_pattern_type_idx')
        ]

    def __str__(self):
        return f"URL Pattern: {self.type}"

    @classmethod
    def get_comparison_pattern(cls):
        """Creates or retrieves the pattern used for college comparison URLs."""
        return cls.objects.get_or_create(
            type='compare-colleges',
            defaults={'id': 102}
        )[0]

    def get_aliases(self):
        """Returns all URL aliases using this pattern."""
        return self.url_aliases.all()


from django.db import models
from django.utils import timezone


class BaseUrlAlias(models.Model):
    """
    Manages URL aliases and their corresponding source URLs.
    This model handles URL redirects and SEO-friendly URLs throughout the application.
    Each alias is associated with a specific URL pattern and includes metadata
    for tracking creation, updates, and SEO properties.
    """
    url_meta_pattern = models.ForeignKey(
        'UrlMetaPattern',  # Use string reference for the related model
        on_delete=models.CASCADE,
        related_name='url_aliases',
        help_text="The pattern type this URL follows"
    )
    source = models.CharField(
        max_length=255,
        unique=True,
        help_text="Original source URL path"
    )
    alias = models.CharField(
        max_length=255,
        unique=True,
        help_text="SEO-friendly URL alias"
    )
    created = models.DateTimeField(
        auto_now_add=True,
        help_text="Creation timestamp"
    )
    updated = models.DateTimeField(
        auto_now=True,
        help_text="Last update timestamp"
    )
    created_by = models.IntegerField(
        help_text="User  ID of creator"
    )
    updated_by = models.IntegerField(
        help_text="User  ID of last updater"
    )
    status = models.PositiveSmallIntegerField(
        default=1,
        help_text="Status flag (1=active, 0=inactive)"
    )
    facet_flag = models.PositiveSmallIntegerField(
        default=0,
        help_text="Indicates if this is a faceted URL (1=yes, 0=no)"
    )
    push_to_sitemap = models.PositiveSmallIntegerField(
        default=1,
        help_text="Include in sitemap (1=yes, 0=no)"
    )
    h1_tag = models.CharField(
        max_length=255,
        default="NA",
        help_text="SEO H1 tag content"
    )
    status_code = models.PositiveSmallIntegerField(
        default=200,
        help_text="HTTP status code"
    )

    class Meta:
        db_table = 'base_url_alias'
        indexes = [
            models.Index(fields=['source']),
            models.Index(fields=['alias']),
            models.Index(fields=['status']),
            models.Index(fields=['url_meta_pattern'])
        ]

    def __str__(self):
        return f"{self.alias} -> {self.source}"

    @staticmethod
    def bulk_create_aliases(aliases_data, user_id=1):
        """
        Efficiently creates multiple URL aliases in bulk.
        
        Args:
            aliases_data: List of dicts with source and alias keys
            user_id: ID of the user creating the aliases
        """
        return BaseUrlAlias.objects.bulk_create([
            BaseUrlAlias(
                source=data['source'],
                alias=data['alias'],
                h1_tag=data['h1_tag'],
                url_meta_pattern_id=data['url_meta_pattern_id'],
                created_by=user_id,
                updated_by=user_id
            ) for data in aliases_data
        ])