from django.urls import path
from .views import (
    ActivityCreateView,
    ActivityListView,
    ActivityView,
    LessonCreateView,
    LessonListView,
    LessonView,
    LoginView, AllStudentsView, StudentInfoView,
    PointRulesView,
    PointsReportsView,
    PointsTransactionsView,
    AdminsInfoView, AdminStudentsView,
    AttendStudentsView, AttendStudentsGetView,
    AttendStudentsDeleteView, AttendStudentsGetAllView,
    PagesView,
    SurahListView,
    VersionView,
    PlaceholderView,
    HadithView,
    UnmemorizedPagesView,
    TestView,
    NoteView,
    StudentBehaviorView,
    GoodBehaviorView,
    StudentBehaviorStatisticsView
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
    path('unmemorized-pages', UnmemorizedPagesView.as_view()),
    path('points/rules', PointRulesView.as_view()),
    path('points/surahs', SurahListView.as_view()),
    path('points/transactions', PointsTransactionsView.as_view()),
    path('points/reports', PointsReportsView.as_view()),


    # System
    path('version', VersionView.as_view()),

    path('ahadith', HadithView.as_view()),

    # Activities and lessons
    path('activities', ActivityView.as_view()),
    path('get/activities', ActivityListView.as_view()),
    path('add/activities', ActivityCreateView.as_view()),
    path('lessons', LessonView.as_view()),
    path('get/lessons', LessonListView.as_view()),
    path('add/lessons', LessonCreateView.as_view()),

    # New endpoints for requested features
    path('tests', TestView.as_view()),
    path('notes', NoteView.as_view()),
    path('behaviors', StudentBehaviorView.as_view()),
    path('good-behaviors', GoodBehaviorView.as_view()),
    path('behaviors/statistics', StudentBehaviorStatisticsView.as_view()),

    # Other placeholder endpoints (to avoid 404)
    path('archive', PlaceholderView.as_view()),
    path('<str:type>/messages', PlaceholderView.as_view()),
]
