
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.db.models import Q

from .models import (
    Post,
    Profile,
    Like,
    Comment,
    Follow,
    Notification,
    Message,
)


# ============================================================
# HOME / PERSONALIZED FEED
# ============================================================

@login_required
def home(request):

    following_users = Follow.objects.filter(
        follower=request.user
    ).values_list(
        "following_id",
        flat=True
    )

    posts = (
        Post.objects.filter(
            Q(author=request.user) |
            Q(author_id__in=following_users)
        )
        .select_related("author")
        .prefetch_related("likes", "comments")
        .order_by("-created_at")
    )

    unread_notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()

    unread_messages = Message.objects.filter(
        receiver=request.user,
        is_read=False
    ).count()

    return render(
        request,
        "social/home.html",
        {
            "posts": posts,
            "unread_notifications": unread_notifications,
            "unread_messages": unread_messages,
        }
    )


# ============================================================
# REGISTER
# ============================================================

def register(request):

    if request.method == "POST":

        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            return render(
                request,
                "social/register.html",
                {
                    "error": "Username and password are required."
                }
            )

        if User.objects.filter(username=username).exists():
            return render(
                request,
                "social/register.html",
                {
                    "error": "Username already exists."
                }
            )

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        Profile.objects.get_or_create(user=user)

        login(request, user)

        return redirect("home")

    return render(
        request,
        "social/register.html"
    )


# ============================================================
# CREATE POST
# ============================================================

@login_required
def create_post(request):

    if request.method == "POST":

        content = request.POST.get("content", "").strip()
        image = request.FILES.get("image")

        if content or image:

            Post.objects.create(
                author=request.user,
                content=content,
                image=image
            )

        return redirect("home")

    return render(
        request,
        "social/create_post.html"
    )


# ============================================================
# POST DETAIL
# ============================================================

@login_required
def post_detail(request, post_id):

    post = get_object_or_404(
        Post.objects.select_related(
            "author"
        ).prefetch_related(
            "likes",
            "comments"
        ),
        id=post_id
    )

    return render(
        request,
        "social/post_detail.html",
        {
            "post": post
        }
    )


# ============================================================
# LIKE / UNLIKE POST
# ============================================================

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

        like.delete()

    else:

        Like.objects.create(
            post=post,
            user=request.user
        )

        if post.author != request.user:

            Notification.objects.create(
                recipient=post.author,
                sender=request.user,
                notification_type="like",
                post=post
            )

    return redirect(
        request.META.get(
            "HTTP_REFERER",
            "home"
        )
    )


# ============================================================
# ADD COMMENT
# ============================================================

@login_required
def add_comment(request, post_id):

    post = get_object_or_404(
        Post,
        id=post_id
    )

    if request.method == "POST":

        content = request.POST.get(
            "content",
            ""
        ).strip()

        if content:

            Comment.objects.create(
                post=post,
                author=request.user,
                content=content
            )

            if post.author != request.user:

                Notification.objects.create(
                    recipient=post.author,
                    sender=request.user,
                    notification_type="comment",
                    post=post
                )

    return redirect(
        request.META.get(
            "HTTP_REFERER",
            "home"
        )
    )


# ============================================================
# SHARE POST
# ============================================================

@login_required
def share_post(request, post_id):

    post = get_object_or_404(
        Post,
        id=post_id
    )

    if request.method != "POST":

        return redirect("home")

    receiver_id = request.POST.get("receiver_id")

    if not receiver_id:

        django_messages.error(
            request,
            "Please select a person to share this post with."
        )

        return redirect("home")

    receiver = get_object_or_404(
        User,
        id=receiver_id
    )

    if receiver == request.user:

        django_messages.error(
            request,
            "You cannot share a post with yourself."
        )

        return redirect("home")

    # Create a message containing the original post.
    Message.objects.create(
        sender=request.user,
        receiver=receiver,
        content="",
        post=post
    )

    # Notify receiver that a post was shared.
    Notification.objects.create(
        recipient=receiver,
        sender=request.user,
        notification_type="message",
        post=post
    )

    django_messages.success(
        request,
        f"Post shared with @{receiver.username}."
    )

    return redirect(
        "chat",
        username=receiver.username
    )


# ============================================================
# SEND SHARED POST
# ============================================================

@login_required
def send_shared_post(request, post_id, username):

    post = get_object_or_404(
        Post,
        id=post_id
    )

    receiver = get_object_or_404(
        User,
        username=username
    )

    if receiver == request.user:

        django_messages.error(
            request,
            "You cannot share a post with yourself."
        )

        return redirect("home")

    if request.method == "POST":

        Message.objects.create(
            sender=request.user,
            receiver=receiver,
            content="",
            post=post
        )

        Notification.objects.create(
            recipient=receiver,
            sender=request.user,
            notification_type="message",
            post=post
        )

        return redirect(
            "chat",
            username=receiver.username
        )

    return redirect(
        "chat",
        username=receiver.username
    )


# ============================================================
# FOLLOW / UNFOLLOW
# ============================================================

@login_required
def follow_user(request, username):

    user_to_follow = get_object_or_404(
        User,
        username=username
    )

    if request.user != user_to_follow:

        follow = Follow.objects.filter(
            follower=request.user,
            following=user_to_follow
        ).first()

        if follow:

            follow.delete()

        else:

            Follow.objects.create(
                follower=request.user,
                following=user_to_follow
            )

            Notification.objects.create(
                recipient=user_to_follow,
                sender=request.user,
                notification_type="follow"
            )

    return redirect(
        "profile",
        username=username
    )


# ============================================================
# PROFILE
# ============================================================

def profile(request, username):

    user = get_object_or_404(
        User,
        username=username
    )

    profile, created = Profile.objects.get_or_create(
        user=user
    )

    posts = (
        Post.objects.filter(
            author=user
        )
        .select_related("author")
        .prefetch_related(
            "likes",
            "comments"
        )
        .order_by("-created_at")
    )

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
        "social/profile.html",
        {
            "profile_user": user,
            "profile": profile,
            "posts": posts,
            "followers_count": followers_count,
            "following_count": following_count,
            "is_following": is_following,
        }
    )


# ============================================================
# EDIT PROFILE
# ============================================================

@login_required
def edit_profile(request):

    profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        profile.bio = request.POST.get(
            "bio",
            ""
        ).strip()

        profile_picture = request.FILES.get(
            "profile_picture"
        )

        if profile_picture:

            profile.profile_picture = profile_picture

        profile.save()

        return redirect(
            "profile",
            username=request.user.username
        )

    return render(
        request,
        "social/edit_profile.html",
        {
            "profile": profile,
            "profile_user": request.user,
        }
    )


# ============================================================
# SEARCH USERS
# ============================================================

@login_required
def search_users(request):

    query = request.GET.get(
        "q",
        ""
    ).strip()

    users = User.objects.none()

    if query:

        users = (
            User.objects.filter(
                username__icontains=query
            )
            .exclude(
                id=request.user.id
            )
            .select_related(
                "profile"
            )
            .order_by(
                "username"
            )
        )

    return render(
        request,
        "social/search.html",
        {
            "query": query,
            "users": users,
        }
    )


# ============================================================
# NOTIFICATIONS
# ============================================================

@login_required
def notifications(request):

    notification_list = (
        Notification.objects.filter(
            recipient=request.user
        )
        .select_related(
            "sender",
            "post"
        )
        .order_by(
            "-created_at"
        )
    )

    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(
        is_read=True
    )

    return render(
        request,
        "social/notifications.html",
        {
            "notifications": notification_list
        }
    )


# ============================================================
# FOLLOWERS LIST
# ============================================================

def followers_list(request, username):

    user = get_object_or_404(
        User,
        username=username
    )

    followers = (
        User.objects.filter(
            following__following=user
        )
        .select_related(
            "profile"
        )
        .order_by(
            "username"
        )
    )

    return render(
        request,
        "social/followers.html",
        {
            "profile_user": user,
            "users": followers,
            "list_type": "Followers",
        }
    )


# ============================================================
# FOLLOWING LIST
# ============================================================

def following_list(request, username):

    user = get_object_or_404(
        User,
        username=username
    )

    following = (
        User.objects.filter(
            followers__follower=user
        )
        .select_related(
            "profile"
        )
        .order_by(
            "username"
        )
    )

    return render(
        request,
        "social/following.html",
        {
            "profile_user": user,
            "users": following,
            "list_type": "Following",
        }
    )


# ============================================================
# MESSAGES / INBOX
# ============================================================

@login_required
def messages(request):

    current_user = request.user

    conversation_user_ids = set(
        Message.objects.filter(
            Q(sender=current_user) |
            Q(receiver=current_user)
        )
        .values_list(
            "sender_id",
            flat=True
        )
    )

    conversation_user_ids.update(
        Message.objects.filter(
            Q(sender=current_user) |
            Q(receiver=current_user)
        )
        .values_list(
            "receiver_id",
            flat=True
        )
    )

    conversation_user_ids.discard(
        current_user.id
    )

    conversation_users = []

    for user_id in conversation_user_ids:

        user = User.objects.select_related(
            "profile"
        ).get(
            id=user_id
        )

        latest_message = (
            Message.objects.filter(
                Q(
                    sender=current_user,
                    receiver=user
                )
                |
                Q(
                    sender=user,
                    receiver=current_user
                )
            )
            .order_by(
                "-created_at"
            )
            .first()
        )

        unread_count = Message.objects.filter(
            sender=user,
            receiver=current_user,
            is_read=False
        ).count()

        conversation_users.append(
            {
                "user": user,
                "latest_message": latest_message,
                "unread_count": unread_count,
            }
        )

    # MOST RECENT MESSAGE ALWAYS AT TOP
    conversation_users.sort(
        key=lambda item: (
            item["latest_message"].created_at
            if item["latest_message"]
            else 0
        ),
        reverse=True
    )

    other_users = (
        User.objects.exclude(
            id=current_user.id
        )
        .exclude(
            id__in=conversation_user_ids
        )
        .select_related(
            "profile"
        )
        .order_by(
            "username"
        )
    )

    unread_messages = Message.objects.filter(
        receiver=current_user,
        is_read=False
    ).count()

    unread_notifications = Notification.objects.filter(
        recipient=current_user,
        is_read=False
    ).count()

    return render(
        request,
        "social/messages.html",
        {
            "conversation_users": conversation_users,
            "users": other_users,
            "unread_messages": unread_messages,
            "unread_notifications": unread_notifications,
        }
    )


# ============================================================
# PRIVATE CHAT
# ============================================================

@login_required
def chat(request, username):

    other_user = get_object_or_404(
        User,
        username=username
    )

    if other_user == request.user:

        return redirect("messages")

    # ========================================================
    # SEND NORMAL MESSAGE
    # ========================================================

    if request.method == "POST":

        content = request.POST.get(
            "content",
            ""
        ).strip()

        if content:

            Message.objects.create(
                sender=request.user,
                receiver=other_user,
                content=content
            )

            Notification.objects.create(
                recipient=other_user,
                sender=request.user,
                notification_type="message"
            )

        return redirect(
            "chat",
            username=other_user.username
        )

    # ========================================================
    # GET CONVERSATION
    # ========================================================

    chat_messages = (
        Message.objects.filter(
            Q(
                sender=request.user,
                receiver=other_user
            )
            |
            Q(
                sender=other_user,
                receiver=request.user
            )
        )
        .select_related(
            "sender",
            "receiver",
            "post",
            "post__author"
        )
        .order_by(
            "created_at"
        )
    )

    # ========================================================
    # MARK RECEIVED MESSAGES AS READ
    # ========================================================

    Message.objects.filter(
        sender=other_user,
        receiver=request.user,
        is_read=False
    ).update(
        is_read=True
    )

    # ========================================================
    # BUILD CHAT LIST
    # ========================================================

    current_user = request.user

    conversation_user_ids = set(
        Message.objects.filter(
            Q(sender=current_user) |
            Q(receiver=current_user)
        )
        .values_list(
            "sender_id",
            flat=True
        )
    )

    conversation_user_ids.update(
        Message.objects.filter(
            Q(sender=current_user) |
            Q(receiver=current_user)
        )
        .values_list(
            "receiver_id",
            flat=True
        )
    )

    conversation_user_ids.discard(
        current_user.id
    )

    conversation_users = []

    for user_id in conversation_user_ids:

        user = User.objects.select_related(
            "profile"
        ).get(
            id=user_id
        )

        latest_message = (
            Message.objects.filter(
                Q(
                    sender=current_user,
                    receiver=user
                )
                |
                Q(
                    sender=user,
                    receiver=current_user
                )
            )
            .order_by(
                "-created_at"
            )
            .first()
        )

        unread_count = Message.objects.filter(
            sender=user,
            receiver=current_user,
            is_read=False
        ).count()

        conversation_users.append(
            {
                "user": user,
                "latest_message": latest_message,
                "unread_count": unread_count,
            }
        )

    # MOST RECENTLY ACTIVE CHAT FIRST
    conversation_users.sort(
        key=lambda item: (
            item["latest_message"].created_at
            if item["latest_message"]
            else 0
        ),
        reverse=True
    )

    other_users = (
        User.objects.exclude(
            id=current_user.id
        )
        .exclude(
            id__in=conversation_user_ids
        )
        .select_related(
            "profile"
        )
        .order_by(
            "username"
        )
    )

    unread_messages = Message.objects.filter(
        receiver=current_user,
        is_read=False
    ).count()

    unread_notifications = Notification.objects.filter(
        recipient=current_user,
        is_read=False
    ).count()

    return render(
        request,
        "social/chat.html",
        {
            "conversation_users": conversation_users,
            "users": other_users,
            "other_user": other_user,
            "chat_messages": chat_messages,
            "unread_messages": unread_messages,
            "unread_notifications": unread_notifications,
        }
    )
