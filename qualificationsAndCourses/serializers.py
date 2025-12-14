from rest_framework import serializers
from .models import Qualifications, Courses

# serializers.py
class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Courses
        fields = ['name', 'grade']



# serializers.py
class QualificationSerializer(serializers.ModelSerializer):
    courses = CourseSerializer(many=True)

    class Meta:
        model = Qualifications
        fields = [
            'id', 'applicant', 'industry', 'name', 'courses',
            'is_verified', 'transcript', 'profile_photo', 'id_document'
        ]
        read_only_fields = ['id', 'applicant']

    def create(self, validated_data):
        courses_data = validated_data.pop('courses', [])
        user = self.context['request'].user
        qualification = Qualifications.objects.create(applicant=user, **validated_data)

        for course_data in courses_data:
            Courses.objects.create(qualification=qualification, **course_data)

        return qualification

    def update(self, instance, validated_data):
        courses_data = validated_data.pop('courses', None)

        # update qualification fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # if courses were included, replace them
        if courses_data is not None:
            instance.courses.all().delete()
            for course_data in courses_data:
                Courses.objects.create(qualification=instance, **course_data)

        return instance

