
from django.urls import path
from . import views


urlpatterns = [

    # =========================
    # HOME
    # =========================

    path(
        '',
        views.home,
        name='home'
    ),

    # =========================
    # REGISTER
    # =========================

    path(
        'register/',
        views.register,
        name='register'
    ),

    # =========================
    # CREATE POST
    # =========================

    path(
        'create-post/',
        views.create_post,
        name='create_post'
    ),

    # =========================
    # LIKE / UNLIKE
    # =========================

    path(
        'like/<int:post_id>/',
        views.like_post,
        name='like_post'
    ),

    # =========================
    # COMMENT
    # =========================

    path(
        'comment/<int:post_id>/',
        views.add_comment,
        name='add_comment'
    ),

    # =========================
    # FOLLOW / UNFOLLOW
    # =========================

    path(
        'follow/<str:username>/',
        views.follow_user,
        name='follow_user'
    ),

    # =========================
    # EDIT PROFILE
    # =========================

    path(
        'edit-profile/',
        views.edit_profile,
        name='edit_profile'
    ),

    # =========================
    # SEARCH USERS
    # =========================

    path(
        'search/',
        views.search_users,
        name='search_users'
    ),

    # =========================
    # PROFILE
    # =========================

    path(
        'profile/<str:username>/',
        views.profile,
        name='profile'
    ),

    # =========================
    # NOTIFICATIONS
    # =========================

    path(
        'notifications/',
        views.notifications,
        name='notifications'
    ),
    
    path(
    'profile/<str:username>/followers/',
    views.followers_list,
    name='followers'
),

path(
    'profile/<str:username>/following/',
    views.following_list,
    name='following'
),

]


