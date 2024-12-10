from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import time


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
            models.Index(fields=['is_stream', 'old_domain_name']),
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

    course_name = models.CharField(max_length=255)
    college = models.ForeignKey(
        College, on_delete=models.CASCADE, related_name='courses', db_index=True
    )
    degree = models.ForeignKey(
        Degree, on_delete=models.SET_NULL, null=True, blank=True, related_name='course'
    )
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, null=True, blank=True, related_name='course'
    )
    level = models.IntegerField(choices=LEVEL_CHOICES)
    status = models.BooleanField(default=True)

    class Meta:
        db_table = 'colleges_courses'
        unique_together = ['course_name', 'college', 'level']
        indexes = [
            models.Index(fields=['degree', 'branch', 'college', 'status']),
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


class CollegeReviews(models.Model):
    college = models.ForeignKey(
        College, on_delete=models.CASCADE, related_name='reviews', db_column='college_id', db_index=True
    )
    overall_rating = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)], db_index=True
    )
    review_text = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'college_reviews'

    def __str__(self):
        return f"Review for {self.college.name} - {self.overall_rating}/100"


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
        ]
        verbose_name = 'College Comparison Data'
        verbose_name_plural = 'College Comparison Data'

    def __str__(self):
        return f"Comparison by User {self.uid}: [{self.college_1}, {self.college_2}, {self.college_3}, {self.college_4}]"



class User(models.Model):
    uid = models.IntegerField(unique=True, primary_key=True)
    domain = models.ForeignKey('Domain', on_delete=models.SET_NULL, null=True, related_name='users')
    current_education_level = models.IntegerField(null=True)

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
    ranking_entity = models.CharField(max_length=255)

    class Meta:
        db_table = 'ranking'
    

    def __str__(self):
        return f"{self.ranking_authority} - {self.ranking_entity}"


class RankingUploadList(models.Model):
    college = models.ForeignKey('College', on_delete=models.CASCADE, related_name='ranking_uploads', db_index=True)
    ranking = models.ForeignKey(Ranking, on_delete=models.CASCADE, related_name='ranking_uploads', db_index=True)
    overall_rank = models.IntegerField()

    class Meta:
        db_table = 'ranking_upload_list'
        

    def __str__(self):
        return f"Ranking for {self.college.name} - Rank: {self.overall_rank}"

