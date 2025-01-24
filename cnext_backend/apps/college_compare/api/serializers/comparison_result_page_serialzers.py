from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist
from  college_compare.models import College, Course, CollegeCourseComparisonFeedback, User, UserReportPreferenceMatrix
 

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
#                 feedback_data[f'course_{i}_id'] = a course_id
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


class UserPreferenceSaveSerializer(serializers.ModelSerializer):
    uid = serializers.IntegerField(required=True)
    course_1 = serializers.IntegerField(required=True)
    course_2 = serializers.IntegerField(required=True)
    course_3 = serializers.IntegerField(required=False, allow_null=True)
    preferences = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        min_length=5,
        max_length=10,
        help_text="List of up to 10 preferences in order, but only the first 5 will be saved."
    )

    
    class Meta:
        model = UserReportPreferenceMatrix
        fields = ['uid', 'course_1', 'course_2', 'course_3', 'preferences']

    def validate(self, data):
        # Define Available Preferences Here
        AVAILABLE_PREFERENCES = [
        "Fees", "Placement", "Scholarship", "People Perception", "Gender Diversity",
        "Alumni Network", "Location", "Faculty & Resources", "Academic Reputation", "Extra Curricular & Resources"
    ]
        # Validate user existence
        if not User.objects.filter(uid=data['uid']).exists():
            raise serializers.ValidationError({"uid": "User ID does not exist."})

        # Validate course existence
        for key in ['course_1', 'course_2', 'course_3']:
            if key in data and data[key] is not None:
                if not Course.objects.filter(id=data[key]).exists():
                    raise serializers.ValidationError({key: f"Course ID {data[key]} does not exist."})

        # Validate preferences using AVAILABLE_PREFERENCES from the model
        invalid_prefs = [p for p in data['preferences'] if p not in AVAILABLE_PREFERENCES]
        if invalid_prefs:
            raise serializers.ValidationError({"preferences": f"Invalid preferences: {invalid_prefs}"})

        # Ensure preferences are unique
        if len(data['preferences']) != len(set(data['preferences'])):
            raise serializers.ValidationError({"preferences": "Preferences should be unique. Duplicates are not allowed."})

        return data

    def create(self, validated_data):
        preferences = validated_data.pop('preferences', [])[:5] 

        user_preference = UserReportPreferenceMatrix.objects.create(
            uid_id=validated_data['uid'],  # Use `_id` to pass the primary key directly
            course_1_id=validated_data['course_1'],
            course_2_id=validated_data['course_2'],
            course_3_id=validated_data['course_3'] if validated_data.get('course_3') else None,
            preference_1=preferences[0] if len(preferences) > 0 else None,
            preference_2=preferences[1] if len(preferences) > 1 else None,
            preference_3=preferences[2] if len(preferences) > 2 else None,
            preference_4=preferences[3] if len(preferences) > 3 else None,
            preference_5=preferences[4] if len(preferences) > 4 else None
        )

        return user_preference
