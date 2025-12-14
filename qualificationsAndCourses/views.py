from .models import Qualifications, Courses 
from .serializers import QualificationSerializer, CourseSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_qualification(request):
    serializer = QualificationSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response({'success': True, 'message': "Qualification with courses saved successfully."}, status=201)
    return Response({'error': serializer.errors}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_courses(request):
    serializer = CourseSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'success': True, 'message': "Course saved successfully"}, status=status.HTTP_201_CREATED)
    return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_qualifications(request):
    qualifications = Qualifications.objects.filter(applicant=request.user)
    serializer = QualificationSerializer(qualifications, many=True)
    return Response({'success': True, 'data': serializer.data, 'message': 'Qualifications fetched successfully.'}, status=status.HTTP_200_OK)

# views.py
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_qualification(request, pk):
    try:
        qualification = Qualifications.objects.get(id=pk, applicant=request.user)
    except Qualifications.DoesNotExist:
        return Response(
            {'error': 'Qualification not found or not owned by user.'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = QualificationSerializer(
        qualification,
        data=request.data,
        partial=True,  # allows PATCH-style updates
        context={'request': request}
    )

    if serializer.is_valid():
        serializer.save()
        return Response({'success': True, 'message': 'Qualification updated successfully.'}, status=status.HTTP_200_OK)

    return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
