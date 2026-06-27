from django.urls import path
from .views import activities, auth, group_session, lessons, student_attend, students, users

urlpatterns = [
     path('', auth.index, name='index'),
     path('login/', auth.login, name='login'),
     path('logout/', auth.logout, name='logout'),

     path('users/add/', users.add_user, name='add_user'),
     path('users/show', users.show_users, name='show_users'),
     path('users/<int:id>/edit/', users.edit_user, name='edit_user'),
     path('users/<int:id>/delete/', users.delete_user, name='delete_user'),

     path('students/add/', students.add, name='add_user'),
     path('students/show', students.show, name='show_users'),
     path('students/<int:id>/details', students.details, name='show_users'),
     path('students/<int:id>/edit/', students.edit, name='edit_user'),
     path('students/<int:id>/delete/', students.delete, name='delete_user'),
     path('memorized/<int:id>/delete/', students.delete_memorized, name='delete_user'),
     path('students/<int:id>/disable/', students.disable, name='disable_user'),
     path('students/<int:id>/enable/', students.enable, name='enable_user'),
     path('students/<int:student_id>/addmemorize/', students.add_memorize, name='edit_user'),

     path('get_pages/<int:section>/', students.get_pages, name='edit_user'),

     path('groupsession/show', group_session.show, name='show_users'),
     path('groupsession/<int:id>/add/', group_session.add, name='add_user'),
     path('groupsession/<int:id>/edit/', group_session.edit, name='edit_user'),
     path('groupsession/<int:old_teacher_id>/changeteacher/', group_session.change_teacher, name='edit_user'),
     path('groupsession/<int:id>/delete/', group_session.delete, name='delete_user'),

     path('attend/<int:id>/add/', student_attend.add, name='add_user'),
     path('attend/show', student_attend.show, name='show_users'),
     path('attend/<str:date>/<int:teacher_id>/edit/', student_attend.edit, name='edit_user'),
     path('attend/<str:date>/<int:teacher_id>/delete/', student_attend.delete, name='delete_user'),

     path('activities/add/', activities.add, name='add_activity'),
     path('activities/show', activities.show, name='show_activities'),
     path('activities/<int:id>/edit/', activities.edit, name='edit_activity'),
     path('activities/<int:id>/delete/', activities.delete, name='delete_activity'),

     path('lessons/add/', lessons.add, name='add_lesson'),
     path('lessons/show', lessons.show, name='show_lessons'),
     path('lessons/<int:id>/edit/', lessons.edit, name='edit_lesson'),
     path('lessons/<int:id>/delete/', lessons.delete, name='delete_lesson'),

]
