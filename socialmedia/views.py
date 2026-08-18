from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from .forms import RegisterForm
from .models import Post, Profile, Like, Comment, Follow


def home(request):
    posts = Post.objects.all().order_by('-created_at')

    return render(request, 'social/home.html', {
        'posts': posts
    })


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()

            # Automatically create profile
            Profile.objects.get_or_create(user=user)

            login(request, user)

            return redirect('home')
    else:
        form = RegisterForm()

    return render(request, 'social/register.html', {
        'form': form
    })


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

    return render(request, 'social/create_post.html')


@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    like = Like.objects.filter(
        post=post,
        user=request.user
    ).first()

    if like:
        # Already liked → Unlike
        like.delete()
    else:
        # Not liked → Like
        Like.objects.create(
            post=post,
            user=request.user
        )

    return redirect('home')


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == 'POST':
        content = request.POST.get('content')

        if content and content.strip():
            Comment.objects.create(
                post=post,
                author=request.user,
                content=content.strip()
            )

    return redirect('home')


@login_required
def follow_user(request, username):
    user_to_follow = get_object_or_404(
        User,
        username=username
    )

    # User cannot follow himself
    if request.user != user_to_follow:

        follow = Follow.objects.filter(
            follower=request.user,
            following=user_to_follow
        ).first()

        if follow:
            # Already following → Unfollow
            follow.delete()
        else:
            # Not following → Follow
            Follow.objects.create(
                follower=request.user,
                following=user_to_follow
            )

    return redirect(
        'profile',
        username=username
    )


def profile(request, username):
    profile_user = get_object_or_404(
        User,
        username=username
    )

    profile, created = Profile.objects.get_or_create(
        user=profile_user
    )

    posts = Post.objects.filter(
        author=profile_user
    ).order_by('-created_at')

    followers_count = profile_user.followers.count()
    following_count = profile_user.following.count()

    is_following = False

    if request.user.is_authenticated:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=profile_user
        ).exists()

    return render(request, 'social/profile.html', {
        'profile_user': profile_user,
        'profile': profile,
        'posts': posts,
        'followers_count': followers_count,
        'following_count': following_count,
        'is_following': is_following,
    })