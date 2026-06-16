from django.urls import path
from .views import (
    LoginView, AllStudentsView, StudentInfoView,
    AdminsInfoView, AdminStudentsView,
    AttendStudentsView, AttendStudentsGetView,
    AttendStudentsDeleteView, AttendStudentsGetAllView,
    PagesView,
    VersionView,
    PlaceholderView,
    HadithView
)

urlpatterns = [
    path('login', LoginView.as_view()),
    path('students', AllStudentsView.as_view()),
    path('student-info', StudentInfoView.as_view()),
    path('admins-info', AdminsInfoView.as_view()),
    path('admin-students', AdminStudentsView.as_view()),

    # Attendance
    path('add/attend', AttendStudentsView.as_view()),
    path('get/attend', AttendStudentsGetView.as_view()),
    path('attend', AttendStudentsDeleteView.as_view()),
    path('get/all/attend', AttendStudentsGetAllView.as_view()),

    # Pages
    path('pages', PagesView.as_view()),

    # System
    path('version', VersionView.as_view()),

    path('ahadith', HadithView.as_view()),

    # Other placeholder endpoints (to avoid 404)
    path('activities', PlaceholderView.as_view()),
    path('get/activities', PlaceholderView.as_view()),
    path('add/activities', PlaceholderView.as_view()),
    path('lessons', PlaceholderView.as_view()),
    path('get/lessons', PlaceholderView.as_view()),
    path('add/lessons', PlaceholderView.as_view()),
    path('archive', PlaceholderView.as_view()),
    path('notes', PlaceholderView.as_view()),
    path('<str:type>/messages', PlaceholderView.as_view()),
]