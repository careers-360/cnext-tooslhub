from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist
from college_compare.models import CollegeCompareData,College,Course


DEVICE_WEB = 1
DEVICE_MOBILE = 2

class CollegeCompareSerializer(serializers.ModelSerializer):
    college_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=True,
        help_text="List of college IDs to compare."
    )
    course_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=True,
        help_text="List of course IDs to compare."
    )

    class Meta:
        model = CollegeCompareData
        fields = ['uid', 'college_ids', 'course_ids', 'device']

    def validate(self, data):
        college_ids = data.get('college_ids', [])
        course_ids = data.get('course_ids', [])
        device = data.get('device')

        
        try:
            device = int(device)
        except (ValueError, TypeError):
            raise serializers.ValidationError("Invalid 'device' value. Must be an integer (1 for web, 2 for mobile).")

        
        if device not in [DEVICE_WEB, DEVICE_MOBILE]:
            raise serializers.ValidationError("Invalid 'device' value. Must be either 'web' or 'mobile'.")

      
        
        max_colleges = 4 if device == DEVICE_WEB else 2

      
        if len(college_ids) > max_colleges:
            raise serializers.ValidationError(
                f"For '{'web' if device == DEVICE_WEB else 'mobile'}' device, at most {max_colleges} colleges can be provided."
            )
        if len(course_ids) > max_colleges:
            raise serializers.ValidationError(
                f"For '{'web' if device == DEVICE_WEB else 'mobile'}' device, at most {max_colleges} courses can be provided."
            )

        if len(college_ids) < 2 or len(course_ids) < 2:
            raise serializers.ValidationError("At least two colleges and courses must be provided for comparison.")

       
        
        if len(college_ids) != len(course_ids):
            raise serializers.ValidationError("The number of 'college_ids' must match the number of 'course_ids'.")

       
        data['device'] = device

        return data

    def create(self, validated_data):
        college_ids = validated_data.pop('college_ids')
        course_ids = validated_data.pop('course_ids')

       
        college_compare_data = {
            'uid': validated_data['uid'],
            'device': validated_data['device']
        }

        
        for i, (college_id, course_id) in enumerate(zip(college_ids, course_ids)):
            field_college = f'college_{i + 1}'
            field_course = f'course_{i + 1}'

            try:
               
                college_instance = College.objects.get(id=college_id)
                college_compare_data[field_college] = college_instance
            except ObjectDoesNotExist:
                raise serializers.ValidationError(f"College with ID {college_id} does not exist.")

            try:
               
                course_instance = Course.objects.get(id=course_id)
                college_compare_data[field_course] = course_instance
            except ObjectDoesNotExist:
                raise serializers.ValidationError(f"Course with ID {course_id} does not exist.")

      
        return CollegeCompareData.objects.create(**college_compare_data)
