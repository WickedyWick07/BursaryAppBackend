from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer
from .models import CustomUser
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """
    Custom token refresh view
    """
    try:
        serializer = TokenRefreshSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except TokenError as e:
        return Response({'detail': 'Token is invalid or expired'}, status=status.HTTP_401_UNAUTHORIZED)

# Create your views here.

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_current_user(request):
    user = request.user
    serializer = UserSerializer(user)
    
    # Return user data in the expected format
    return Response({
        'user': serializer.data
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data.get('email')
        password = serializer.validated_data.get('password')

        user = authenticate(email=email, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)
            user_serializer = UserSerializer(user)
            
            return Response({
                'success': True, 
                'message': 'Login Successful', 
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': user_serializer.data  # Add user data
            }, status=status.HTTP_200_OK)
        else: 
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_400_BAD_REQUEST) 

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save() 
        refresh = RefreshToken.for_user(user)
        user_serializer = UserSerializer(user)
        
        return Response({
            'success': True,
            'message': 'Registration Successful',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': user_serializer.data  # Add user data
        }, status=status.HTTP_201_CREATED)  
    else: 
        return Response({
            'error': serializer.errors  # Fix: was user.errors
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_all_users(request): 

    try:
        users = CustomUser.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response({
            'users': serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)