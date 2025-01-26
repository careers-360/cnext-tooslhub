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

#         return data

#     def create(self, validated_data):
#         feedback_data = {
#             'uid': validated_data['uid'],
#             'voted_college_id': validated_data['voted_college'],
#             'voted_course_id': validated_data['voted_course'],
#             'createdBy': str(validated_data['uid']),
#         }

#         for i, (college_id, course_id) in enumerate(zip(validated_data['college_ids'], validated_data['course_ids']), 1):
#             feedback_data[f'college_{i}_id'] = college_id
#             feedback_data[f'course_{i}_id'] = course_id

#         return CollegeCourseComparisonFeedback.objects.create(**feedback_data)



class FeedbackSubmitSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
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
        fields = ['id', 'uid', 'voted_college', 'voted_course', 'college_ids', 'course_ids']

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

    def create_or_update(self, validated_data):
        feedback_id = validated_data.get('id')
        feedback_data = {
            'uid': validated_data['uid'],
            'voted_college_id': validated_data['voted_college'],
            'voted_course_id': validated_data['voted_course'],
            'updatedBy': str(validated_data['uid']),
        }

        for i, (college_id, course_id) in enumerate(zip(validated_data['college_ids'], validated_data['course_ids']), 1):
            feedback_data[f'college_{i}_id'] = college_id
            feedback_data[f'course_{i}_id'] = course_id

        if feedback_id:
            instance = CollegeCourseComparisonFeedback.objects.filter(id=feedback_id).first()
            if instance:
                for key, value in feedback_data.items():
                    setattr(instance, key, value)
                instance.save()
                return instance, "Feedback updated successfully"
            
        instance = CollegeCourseComparisonFeedback.objects.create(**feedback_data, createdBy=str(validated_data['uid']))
        return instance, "Feedback submitted successfully"
    


class UserPreferenceSaveSerializer(serializers.ModelSerializer):
    uid = serializers.IntegerField(required=False)  # Optional for partial updates
    course_1 = serializers.IntegerField(required=False, allow_null=True)
    course_2 = serializers.IntegerField(required=False, allow_null=True)
    course_3 = serializers.IntegerField(required=False, allow_null=True)
    preferences = serializers.ListField(
        child=serializers.CharField(),
        required=False,  # Optional for partial updates
        min_length=5,
        max_length=10
    )

    AVAILABLE_PREFERENCES = {
        "Fees", "Placement", "Scholarship", "People Perception", "Gender Diversity",
        "Alumni Network", "Location", "Faculty & Resources", "Academic Reputation", 
        "Extra Curricular & Resources"
    }

    class Meta:
        model = UserReportPreferenceMatrix
        fields = ['uid', 'course_1', 'course_2', 'course_3', 'preferences']

    def validate(self, data):
        if 'uid' in data:
            user_exists = User.objects.filter(uid=data.get('uid')).exists()
            if not user_exists:
                raise serializers.ValidationError({"uid": "User ID does not exist."})

        course_ids = set()
        if 'course_1' in data:
            course_ids.add(data['course_1'])
        if 'course_2' in data:
            course_ids.add(data['course_2'])
        if 'course_3' in data:
            course_ids.add(data['course_3'])
        course_ids.discard(None)  # Remove None values if any course field is missing

        if course_ids:
            existing_courses = Course.objects.filter(id__in=course_ids).values_list('id', flat=True)
            if len(existing_courses) != len(course_ids):
                raise serializers.ValidationError({"courses": "One or more course IDs do not exist."})

        if 'preferences' in data:
            preferences_set = set(data['preferences'])
            invalid_prefs = preferences_set - self.AVAILABLE_PREFERENCES
            if invalid_prefs:
                raise serializers.ValidationError({"preferences": f"Invalid preferences: {invalid_prefs}"})

            if len(preferences_set) != len(data['preferences']):
                raise serializers.ValidationError({"preferences": "Duplicate preferences not allowed."})

        return data

    def create(self, validated_data):
        preferences = validated_data.pop('preferences', [])[:5]
        preference_dict = {
            f'preference_{i+1}': pref 
            for i, pref in enumerate(preferences)
        }
        
        return UserReportPreferenceMatrix.objects.create(
            uid_id=validated_data.get('uid'),
            course_1_id=validated_data.get('course_1'),
            course_2_id=validated_data.get('course_2'),
            course_3_id=validated_data.get('course_3'),
            **preference_dict
        )
    @staticmethod
    def update_user_preference_matrix(user_preference_id, update_data):
        try:
            user_preference = UserReportPreferenceMatrix.objects.get(id=user_preference_id)

            # Validate and update the uid if provided
            if 'uid' in update_data:
                user_instance = User.objects.get(uid=update_data['uid'])  # Get the User instance
                user_preference.uid = user_instance  # Assign the User instance to the foreign key

            # Other field updates (fees_budget, location_states, exams) stay the same as before
            if 'fees_budget' in update_data:
                fees_budget = update_data['fees_budget']
                if fees_budget and not isinstance(fees_budget, str):
                    raise serializers.ValidationError({"fees_budget": "Must be a string representation of budget."})
                user_preference.fees_budget = fees_budget

            if 'location_states' in update_data:
                location_states = update_data['location_states']
                if location_states is not None:
                    if not isinstance(location_states, list):
                        raise serializers.ValidationError({"location_states": "Must be a list of states."})
                    user_preference.location_states = location_states

            if 'exams' in update_data:
                exams = update_data['exams']
                if exams is not None:
                    if not isinstance(exams, list):
                        raise serializers.ValidationError({"exams": "Must be a list of exam names."})
                    user_preference.exams = exams

            user_preference.save()
            return user_preference

        except UserReportPreferenceMatrix.DoesNotExist:
            raise serializers.ValidationError({"error": f"No UserReportPreferenceMatrix found with id {user_preference_id}."})
        