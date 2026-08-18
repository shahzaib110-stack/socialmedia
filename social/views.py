
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from .models import (
    Post,
    Profile,
    Like,
    Comment,
    Follow,
    Notification
)


# =========================
# HOME / PERSONALIZED FEED
# =========================

@login_required
def home(request):

    following_users = Follow.objects.filter(
        follower=request.user
    ).values_list(
        'following_id',
        flat=True
    )

    posts = Post.objects.filter(
        Q(author=request.user) |
        Q(author_id__in=following_users)
    ).order_by('-created_at')

    return render(
        request,
        'social/home.html',
        {
            'posts': posts
        }
    )


# =========================
# REGISTER
# =========================

def register(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(
            username=username
        ).exists():

            return render(
                request,
                'social/register.html',
                {
                    'error': 'Username already exists.'
                }
            )

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        Profile.objects.get_or_create(
            user=user
        )

        login(
            request,
            user
        )

        return redirect('home')

    return render(
        request,
        'social/register.html'
    )


# =========================
# CREATE POST
# =========================

@login_required
def create_post(request):

    if request.method == 'POST':

        content = request.POST.get('content')
        image = request.FILES.get('image')

        if content or image:

            Post.objects.create(
                author=request.user,
                content=content or '',
                image=image
            )

        return redirect('home')

    return render(
        request,
        'social/create_post.html'
    )


# =========================
# LIKE / UNLIKE POST
# =========================

@login_required
def like_post(request, post_id):

    post = get_object_or_404(
        Post,
        id=post_id
    )

    like = Like.objects.filter(
        post=post,
        user=request.user
    ).first()

    if like:

        # Unlike
        like.delete()

    else:

        # Like
        Like.objects.create(
            post=post,
            user=request.user
        )

        # Don't notify yourself
        if post.author != request.user:

            Notification.objects.create(
                recipient=post.author,
                sender=request.user,
                notification_type='like',
                post=post
            )

    return redirect('home')


# =========================
# ADD COMMENT
# =========================

@login_required
def add_comment(request, post_id):

    post = get_object_or_404(
        Post,
        id=post_id
    )

    if request.method == 'POST':

        content = request.POST.get('content')

        if content and content.strip():

            Comment.objects.create(
                post=post,
                author=request.user,
                content=content.strip()
            )

            # Don't notify yourself
            if post.author != request.user:

                Notification.objects.create(
                    recipient=post.author,
                    sender=request.user,
                    notification_type='comment',
                    post=post
                )

    return redirect('home')


# =========================
# FOLLOW / UNFOLLOW
# =========================

@login_required
def follow_user(request, username):

    user_to_follow = get_object_or_404(
        User,
        username=username
    )

    # Cannot follow yourself
    if request.user != user_to_follow:

        follow = Follow.objects.filter(
            follower=request.user,
            following=user_to_follow
        ).first()

        if follow:

            # Already following → Unfollow
            follow.delete()

        else:

            # Follow
            Follow.objects.create(
                follower=request.user,
                following=user_to_follow
            )

            # Notification
            Notification.objects.create(
                recipient=user_to_follow,
                sender=request.user,
                notification_type='follow'
            )

    return redirect(
        'profile',
        username=username
    )


# =========================
# PROFILE
# =========================

def profile(request, username):

    user = get_object_or_404(
        User,
        username=username
    )

    profile, created = Profile.objects.get_or_create(
        user=user
    )

    posts = Post.objects.filter(
        author=user
    ).order_by('-created_at')

    followers_count = user.followers.count()

    following_count = user.following.count()

    is_following = False

    if request.user.is_authenticated:

        is_following = Follow.objects.filter(
            follower=request.user,
            following=user
        ).exists()

    return render(
        request,
        'social/profile.html',
        {
            'profile_user': user,
            'profile': profile,
            'posts': posts,
            'followers_count': followers_count,
            'following_count': following_count,
            'is_following': is_following,
        }
    )


# =========================
# EDIT PROFILE
# =========================

@login_required
def edit_profile(request):

    profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    if request.method == 'POST':

        bio = request.POST.get(
            'bio',
            ''
        ).strip()

        profile.bio = bio

        profile_picture = request.FILES.get(
            'profile_picture'
        )

        if profile_picture:

            profile.profile_picture = profile_picture

        profile.save()

        return redirect(
            'profile',
            username=request.user.username
        )

    return render(
        request,
        'social/edit_profile.html',
        {
            'profile': profile,
            'profile_user': request.user,
        }
    )


# =========================
# SEARCH USERS
# =========================

@login_required
def search_users(request):

    query = request.GET.get(
        'q',
        ''
    ).strip()

    users = User.objects.none()

    if query:

        users = User.objects.filter(
            username__icontains=query
        ).exclude(
            id=request.user.id
        ).order_by('username')

    return render(
        request,
        'social/search.html',
        {
            'query': query,
            'users': users,
        }
    )


# =========================
# NOTIFICATIONS
# =========================

@login_required
def notifications(request):

    notification_list = Notification.objects.filter(
        recipient=request.user
    ).select_related(
        'sender',
        'post'
    ).order_by('-created_at')

    return render(
        request,
        'social/notifications.html',
        {
            'notifications': notification_list
        }
    )


# =========================
# FOLLOWERS LIST
# =========================

def followers_list(request, username):

    user = get_object_or_404(
        User,
        username=username
    )

    followers = User.objects.filter(
        following__following=user
    ).select_related(
        'profile'
    ).order_by('username')

    return render(
        request,
        'social/followers.html',
        {
            'profile_user': user,
            'users': followers,
            'list_type': 'Followers',
        }
    )


# =========================
# FOLLOWING LIST
# =========================

def following_list(request, username):

    user = get_object_or_404(
        User,
        username=username
    )

    following = User.objects.filter(
        followers__follower=user
    ).select_related(
        'profile'
    ).order_by('username')

    return render(
        request,
        'social/following.html',
        {
            'profile_user': user,
            'users': following,
            'list_type': 'Following',
        }
    )

