from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import time



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

class Location(models.Model):
    loc_string = models.TextField(null=True, blank=True)
    country_id = models.IntegerField(default=1)
    state_id = models.IntegerField(null=True, blank=True)
    city_id = models.IntegerField(null=True, blank=True)
    status = models.BooleanField(default=True)

    class Meta:
        db_table = 'location'
        indexes = [
            models.Index(fields=['country_id', 'state_id', 'city_id', 'status']),
        ]
        app_label = 'college_compare'


    def __str__(self):
        return self.loc_string or "Location Not Available"


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
    short_name = models.CharField(max_length=50, null=True, blank=True)
    published = models.CharField(max_length=20, default='published', db_index=True)
    status = models.BooleanField(default=True)
    ownership = models.IntegerField(choices=OWNERSHIP_CHOICES)
    institute_type_1 = models.IntegerField(choices=INSTITUTE_TYPE_CHOICES, null=True, blank=True)
    institute_type_2 = models.IntegerField(choices=INSTITUTE_TYPE_CHOICES, null=True, blank=True)
    type_of_entity = models.IntegerField(choices=ENTITY_TYPE_CHOICES, null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)
    campus_size = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    year_of_establishment = models.IntegerField(null=True, blank=True)
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

    class Meta:
        db_table = 'colleges'
        verbose_name_plural = 'Colleges'
        ordering = ['name']
        indexes = [
            models.Index(fields=['published', 'name']),
            models.Index(fields=['country_id']),
            models.Index(fields=['published', 'status', 'country_id']),
        ]

    def __str__(self):
        return self.name

    def ownership_display(self):
        return dict(self.OWNERSHIP_CHOICES).get(self.ownership, '-')

    def type_of_institute(self):
        type_mapping = {
            (1, 1): 'Central University',
            (2, 2): 'State University',
            (3, 3): 'Deemed to be University',
            (4, 4): 'Institute of National Importance',
            (5, 5): 'Institute of Eminence',
        }
        type_combination = type_mapping.get((self.institute_type_1, self.institute_type_2), None)

        if type_combination:
            return type_combination

        if self.institute_type_1:
            return dict(self.INSTITUTE_TYPE_CHOICES).get(self.institute_type_1, '-')
        if self.institute_type_2:
            return dict(self.INSTITUTE_TYPE_CHOICES).get(self.institute_type_2, '-')
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
    stream = models.ForeignKey('Domain', on_delete=models.CASCADE, db_index=True,db_column="stream_id" ,null=True, blank=True)

    class Meta:
        db_table = 'college_placements'
        indexes = [
            models.Index(fields=['college', 'year', 'intake_year', 'levels']),
            models.Index(fields=['published']),
            models.Index(fields=['stream']),  
            
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



class Course(models.Model):
    LEVEL_CHOICES = [
        (1, 'Undergraduate'),
        (2, 'Postgraduate')
    ]

    STUDY_MODE_CHOICES = [
        (1, 'online'),
        (2, 'offline')
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

    class Meta:
        db_table = 'colleges_courses'
        unique_together = ['course_name', 'college', 'level']
        indexes = [
            models.Index(fields=['degree', 'branch', 'college', 'status']),
             models.Index(fields=['degree_domain']),
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



# class CollegeReviews(models.Model):
#     college = models.ForeignKey(
#         College, on_delete=models.CASCADE, related_name='reviews', db_column='college_id', db_index=True
#     )
#     overall_rating = models.IntegerField(
#         validators=[MinValueValidator(0), MaxValueValidator(100)], db_index=True
#     )
#     review_text = models.TextField(null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         db_table = 'college_reviews'



class CollegeReviews(models.Model):
    college = models.ForeignKey(
        'College', 
        on_delete=models.CASCADE, 
        related_name='reviews',
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
   
    status = models.IntegerField(default=1)

    class Meta:
        db_table = 'ranking'

class RankingUploadList(models.Model):
    college = models.ForeignKey(
        'College',
        on_delete=models.CASCADE,
        related_name='ranking_uploads',
        db_index=True,db_column="college_id"
    )
    ranking = models.ForeignKey(
        'Ranking',
        on_delete=models.CASCADE,
        related_name='upload_list',
        db_index=True,
        db_column='ranking_id'
    )
    year = models.IntegerField(db_index=True)
    published = models.BooleanField(default=True)
    overall_rank = models.IntegerField(null=True, blank=True)
    overall_rating = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'ranking_upload_list'
        indexes = [
            models.Index(fields=['college', 'ranking', 'year']),
            models.Index(fields=['year']),
            models.Index(fields=['published']),
        ]

    def __str__(self):
        return f"{self.college.name} - {self.ranking.ranking_authority} ({self.year})"


class FeeBifurcation(models.Model):
    college_course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='fees', db_index=True)
    category = models.CharField(max_length=50)  
    total_fees = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'fees_bifurcations'
        indexes = [
            models.Index(fields=['college_course', 'category']),
        ]


class Exam(models.Model):
    exam_name = models.CharField(max_length=255)
    exam_short_name = models.CharField(max_length=50, null=True, blank=True)
    super_parent_id = models.IntegerField()
    instance_year = models.IntegerField()  
    status = models.CharField(max_length=20)

    class Meta:
        db_table = 'exams'
        indexes = [
            models.Index(fields=['exam_name', 'exam_short_name']),
            models.Index(fields=['instance_year']), 
        ]

    def __str__(self):
        return self.exam_short_name or self.exam_name


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



class CutoffData(models.Model):
    college = models.ForeignKey('College', on_delete=models.CASCADE, db_index=True)
    college_course = models.ForeignKey('Course', on_delete=models.CASCADE, db_index=True)
    round = models.CharField(max_length=255)
    opening_rank = models.FloatField()  
    closing_rank = models.FloatField() 
    category_of_admission = models.CharField(max_length=10,default=1)  
    caste_id = models.CharField(max_length=10, null=True, blank=True) 
    year = models.IntegerField()  
    exam_sub_exam_id = models.IntegerField()  
    branch_id = models.IntegerField()  

    class Meta:
        db_table = 'cutoff_data' 
        indexes = [
            models.Index(fields=['college', 'college_course']),
            models.Index(fields=['category_of_admission']),
            models.Index(fields=['round']),
            models.Index(fields=['year']),
            models.Index(fields=['exam_sub_exam_id']),
            models.Index(fields=['branch_id']),
        ]

    def __str__(self):
        return f"Cutoff Data for {self.college.name} - {self.college_course.course_name} ({self.round})"



