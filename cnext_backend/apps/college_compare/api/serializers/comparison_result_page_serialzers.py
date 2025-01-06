from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist
from  college_compare.models import College, Course, CollegeCourseComparisonFeedback

# class FeedbackSubmitSerializer(serializers.ModelSerializer):
#     voted_college = serializers.IntegerField(required=True)
#     voted_course = serializers.IntegerField(required=True)
#     college_ids = serializers.ListField(
#         child=serializers.IntegerField(),
#         write_only=True,
#         required=True,
#         min_length=2,
#         max_length=3,
#         help_text="List of college IDs to compare (2-3 colleges)"
#     )
#     course_ids = serializers.ListField(

        
#         child=serializers.IntegerField(),
#         write_only=True,
#         required=True,
#         min_length=2,
#         max_length=3,
#         help_text="List of course IDs to compare (2-3 courses)"
#     )

#     class Meta:
#         model = CollegeCourseComparisonFeedback
#         fields = ['uid', 'voted_college', 'voted_course', 'college_ids', 'course_ids']

#     def validate(self, data):
#         college_ids = data.get('college_ids', [])
#         course_ids = data.get('course_ids', [])
#         voted_college = data.get('voted_college')
#         voted_course = data.get('voted_course')

#         if len(college_ids) != len(course_ids):
#             raise serializers.ValidationError("The number of college_ids must match the number of course_ids.")

#         if voted_college not in college_ids:
#             raise serializers.ValidationError("voted_college must be one of the colleges being compared.")
#         if voted_course not in course_ids:
#             raise serializers.ValidationError("voted_course must be one of the courses being compared.")

#         self.college_ids = college_ids
#         self.course_ids = course_ids
        
#         return data

#     def create(self, validated_data):
#         college_ids = self.college_ids
#         course_ids = self.course_ids

#         feedback_data = {
#             'uid': validated_data['uid'],
#             'voted_college_id': validated_data['voted_college'],
#             'voted_course_id': validated_data['voted_course'],
#             'createdBy': str(validated_data['uid'])
#         }

#         for i, (college_id, course_id) in enumerate(zip(college_ids, course_ids), 1):
#             try:
#                 College.objects.get(id=college_id)
#                 feedback_data[f'college_{i}_id'] = college_id
#             except ObjectDoesNotExist:
#                 raise serializers.ValidationError(f"College with ID {college_id} does not exist.")

#             try:
#                 Course.objects.get(id=course_id)
#                 feedback_data[f'course_{i}_id'] = course_id
#             except ObjectDoesNotExist:
#                 raise serializers.ValidationError(f"Course with ID {course_id} does not exist.")

#         return CollegeCourseComparisonFeedback.objects.create(**feedback_data)

class FeedbackSubmitSerializer(serializers.ModelSerializer):
    voted_college = serializers.IntegerField(required=True)
    voted_course = serializers.IntegerField(required=True)
    college_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True,
        min_length=2,
        max_length=3,
        help_text="List of college IDs to compare (2-3 colleges)"
    )
    course_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True,
        min_length=2,
        max_length=3,
        help_text="List of course IDs to compare (2-3 courses)"
    )

    class Meta:
        model = CollegeCourseComparisonFeedback
        fields = ['uid', 'voted_college', 'voted_course', 'college_ids', 'course_ids']

    def validate(self, data):
        college_ids = data.get('college_ids', [])
        course_ids = data.get('course_ids', [])
        voted_college = data.get('voted_college')
        voted_course = data.get('voted_course')

        if len(college_ids) != len(course_ids):
            raise serializers.ValidationError("The number of college_ids must match the number of course_ids.")

        if voted_college not in college_ids:
            raise serializers.ValidationError("voted_college must be one of the colleges being compared.")
        if voted_course not in course_ids:
            raise serializers.ValidationError("voted_course must be one of the courses being compared.")

        return data

    def create(self, validated_data):
        feedback_data = {
            'uid': validated_data['uid'],
            'voted_college_id': validated_data['voted_college'],
            'voted_course_id': validated_data['voted_course'],
            'createdBy': str(validated_data['uid']),
        }

        for i, (college_id, course_id) in enumerate(zip(validated_data['college_ids'], validated_data['course_ids']), 1):
            feedback_data[f'college_{i}_id'] = college_id
            feedback_data[f'course_{i}_id'] = course_id

        return CollegeCourseComparisonFeedback.objects.create(**feedback_data)
