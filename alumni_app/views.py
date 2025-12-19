from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Alumni, Adminn, Notification, Feedback, Event, Connection, Post, Message, ChatRoom, ClearedChat
from django.utils import timezone
from django.db import models
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def send_registration_email(alumni):
    """Send registration confirmation email to alumni"""
    subject = 'Welcome to Global Alumni Connect - Registration Successful'
    message = f"""
    Dear {alumni.first_name} {alumni.last_name},

    Thank you for registering with Global Alumni Connect! Your registration has been received successfully.

    Your registration details:
    Username: {alumni.username}
    Email: {alumni.email}
    Name: {alumni.first_name} {alumni.last_name}
    Graduation Year: {alumni.graduation_year}
    Degree: {alumni.degree}
    Profession: {alumni.profession}
    Company: {alumni.company}
    Industry: {alumni.industry}
    Location: {alumni.location}
    

    Please note that your account is currently pending admin approval. You will receive another email once your account is activated.

    Best regards,
    Global Alumni Connect Team
    """
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[alumni.email],
        fail_silently=False,
    )

def send_account_activation_email(alumni):
    """Send account activation email to alumni"""
    subject = 'Your Global Alumni Connect Account is Now Active'
    message = f"""
    Dear {alumni.first_name} {alumni.last_name},

    Great news! Your Global Alumni Connect account has been activated by the administrator.

    You can now log in to your account using your username and password.

    Your Login details are:
    Username: {alumni.username}
    Password: {alumni.password}

    Best regards,
    Global Alumni Connect Team
    """
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[alumni.email],
        fail_silently=False,
    )

def send_account_deactivation_email(alumni):
    """Send account deactivation email to alumni"""
    subject = 'Your Global Alumni Connect Account has been Disabled'
    message = f"""
    Dear {alumni.first_name} {alumni.last_name},

    This email is to inform you that your Global Alumni Connect account has been disabled by the administrator.

    You will no longer be able to log in to your account. If you believe this is a mistake, please contact the administrator.

    Best regards,
    Global Alumni Connect Team
    """
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[alumni.email],
        fail_silently=False,
    )

@never_cache
def index(request):
   

    # Get featured alumni for spotlight (active alumni with profile pictures)
    featured_alumni = Alumni.objects.filter(
        is_active=True,
        profile_pic__isnull=False
    ).order_by('?')[:4]  # Random 4 alumni

   
   

    context = {
        
       
        'featured_alumni': featured_alumni,
        
    }
    return render(request, 'alumni_app/index.html', context)

@never_cache
def register(request):
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        graduation_year = request.POST.get('graduation_year')
        degree = request.POST.get('degree')
        profession = request.POST.get('profession')
        company = request.POST.get('company')
        industry = request.POST.get('industry')
        location = request.POST.get('location')
        bio = request.POST.get('bio')
        profile_pic = request.FILES.get('profile_pic')

        # Basic validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect('register')
        
        if Alumni.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('register')
        
        if Alumni.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect('register')

        # Create temporary alumni object for email
        temp_alumni = Alumni(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            graduation_year=graduation_year,
            degree=degree,
            profession=profession,
            company=company,
            industry=industry,
            location=location,
            bio=bio,
            profile_pic=profile_pic,
            is_active=False
        )

        # Try to send registration email first
        try:
            send_registration_email(temp_alumni)
            # If email sent successfully, save the alumni record
            temp_alumni.save()
            messages.success(request, 'Registration successful! Please check your email for your Credentials.')
            return redirect('login')
        except Exception as e:
            messages.error(request, 'Registration failed. Could not send confirmation email. Please try again, check your email.')
            print(f"Error sending registration email: {e}")
            return redirect('register')
    
    context = {
        'RECAPTCHA_SITE_KEY': settings.RECAPTCHA_SITE_KEY
    }
    return render(request, 'alumni_app/register.html', context)

@never_cache
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type')
        
        if user_type == 'alumni':
            try:
                alumni = Alumni.objects.get(username=username, password=password)
                if not alumni.is_active:
                    messages.error(request, "Your account is Inactive. Please wait for admin approval.")
                    return redirect('login')
                
                # Store user in session
                request.session['alumni_id'] = alumni.id
                request.session['alumni_username'] = alumni.username
                request.session['is_admin'] = False
                return redirect('alumni_dashboard')
            except Alumni.DoesNotExist:
                messages.error(request, "Invalid credentials")
                return redirect('login')
        
        elif user_type == 'admin':
            try:
                admin = Adminn.objects.get(username=username, password=password)
                # Store admin in session
                request.session['admin_id'] = admin.id
                request.session['is_admin'] = True
                return redirect('admin_dashboard')
            except Adminn.DoesNotExist:
                messages.error(request, "Invalid admin credentials")
                return redirect('login')
    
    return render(request, 'alumni_app/login.html')

@never_cache
def alumni_dashboard(request):
    if not request.session.get('alumni_id') or request.session.get('is_admin'):
        return redirect('login')
    
    alumni = Alumni.objects.get(id=request.session['alumni_id'])
    
    # Get connected alumni
    connections = Connection.objects.filter(
        models.Q(sender=alumni) | models.Q(receiver=alumni),
        status='accepted'
    ).order_by('-updated_at')  # Order by most recent first
    
    connected_alumni = []
    for connection in connections:
        if connection.sender == alumni:
            connected_alumni.append(connection.receiver)
        else:
            connected_alumni.append(connection.sender)
    
    # Get pending connection requests
    pending_requests = Connection.objects.filter(receiver=alumni, status='pending')
    
    # Get upcoming events
    upcoming_events = Event.objects.filter(
        is_active=True,
        date__gte=timezone.now()
    ).order_by('date')[:2]
    
    total_upcoming_events = Event.objects.filter(
        is_active=True,
        date__gte=timezone.now()
    ).count()

    # Get unread messages
    unread_messages = Message.objects.filter(
        receiver=alumni,
        is_read=False
    ).select_related('sender').order_by('-timestamp')[:5]

    # Get unread messages count
    unread_messages_count = Message.objects.filter(
        receiver=alumni,
        is_read=False
    ).count()
    
    context = {
        'alumni': alumni,
        'connected_alumni': connected_alumni[:2],        
        'pending_requests': pending_requests,
        'upcoming_events': upcoming_events,
        'total_upcoming_events': total_upcoming_events,
        'unread_messages': unread_messages,
        'unread_messages_count': unread_messages_count
    }
    return render(request, 'alumni_app/alumni_dashboard.html', context)

@never_cache
def admin_dashboard(request):
    if not request.session.get('admin_id') or not request.session.get('is_admin'):
        return redirect('login')
    
    alumni_list = Alumni.objects.all()
    feedback_list = Feedback.objects.filter(is_resolved=False)
    
    # Event statistics
    total_events = Event.objects.count()
    upcoming_events = Event.objects.filter(date__gte=timezone.now(), is_active=True).count()
    past_events = Event.objects.filter(date__lt=timezone.now()).count()
    recent_events = Event.objects.filter(is_active=True).order_by('-date')[:5]
    
    context = {
        'alumni_list': alumni_list,
        'feedback_list': feedback_list,
        'total_events': total_events,
        'upcoming_events': upcoming_events,
        'past_events': past_events,
        'recent_events': recent_events
    }
    return render(request, 'alumni_app/admin_dashboard.html', context)

@never_cache
def alumni_gallery(request):
    if not request.session.get('alumni_id') or request.session.get('is_admin'):
        return redirect('login')
    
    current_alumni = Alumni.objects.get(id=request.session['alumni_id'])
    alumni_list = Alumni.objects.filter(is_active=True).exclude(id=current_alumni.id)
    
    # Handle search functionality
    search_query = request.GET.get('search', '')
    profession_filter = request.GET.get('profession', '')
    location_filter = request.GET.get('location', '')
    
    if search_query:
        alumni_list = alumni_list.filter(
            models.Q(first_name__icontains=search_query) |
            models.Q(last_name__icontains=search_query)
        )
    
    if profession_filter:
        alumni_list = alumni_list.filter(profession__icontains=profession_filter)
    
    if location_filter:
        alumni_list = alumni_list.filter(location__icontains=location_filter)
    
    # Get connection status for each alumni
    for alumni in alumni_list:
        connection = Connection.objects.filter(
            models.Q(sender=current_alumni, receiver=alumni) |
            models.Q(sender=alumni, receiver=current_alumni),
            status='accepted'
        ).first()
        alumni.is_connected = True if connection else False
    
    return render(request, 'alumni_app/alumni_gallery.html', {
        'alumni_list': alumni_list,
        'search_query': search_query,
        'profession_filter': profession_filter,
        'location_filter': location_filter
    })

@never_cache
def notifications(request):
    if not request.session.get('alumni_id') or request.session.get('is_admin'):
        return redirect('login')
    
    alumni = Alumni.objects.get(id=request.session['alumni_id'])
    notifications = Notification.objects.filter(alumni=alumni).order_by('-created_at')
    
    # Mark notifications as read when viewed
    Notification.objects.filter(alumni=alumni, is_read=False).update(is_read=True)
    
    return render(request, 'alumni_app/notifications.html', {'notifications': notifications})

@never_cache
def submit_feedback(request):
    if not request.session.get('alumni_id') or request.session.get('is_admin'):
        return redirect('login')
    
    if request.method == 'POST':
        message = request.POST.get('message')
        alumni = Alumni.objects.get(id=request.session['alumni_id'])
        
        feedback = Feedback(alumni=alumni, message=message)
        feedback.save()
        
        messages.success(request, 'Feedback submitted successfully!')
        return redirect('alumni_dashboard')
    
    return render(request, 'alumni_app/feedback.html')

@never_cache
def resolve_feedback(request, feedback_id):
    if not request.session.get('admin_id') or not request.session.get('is_admin'):
        return redirect('login')
    
    feedback = Feedback.objects.get(id=feedback_id)
    feedback.is_resolved = True
    feedback.save()
    
    # Create notification for the alumni who submitted the feedback
    Notification.objects.create(
        alumni=feedback.alumni,
        message="Your feedback has been resolved by the admin"
    )
    
    messages.success(request, 'Feedback marked as resolved')
    return redirect('admin_dashboard')

@never_cache
def toggle_alumni_status(request, alumni_id):
    if not request.session.get('admin_id') or not request.session.get('is_admin'):
        return redirect('login')
    
    alumni = Alumni.objects.get(id=alumni_id)
    alumni.is_active = not alumni.is_active
    alumni.save()
    
    # Send appropriate email based on the new status
    try:
        if alumni.is_active:
            send_account_activation_email(alumni)
            messages.success(request, f'Alumni account enabled successfully. Notification email sent.')
        else:
            send_account_deactivation_email(alumni)
            messages.success(request, f'Alumni account disabled successfully. Notification email sent.')
    except Exception as e:
        messages.warning(request, f'Status updated but there was an error sending the notification email.')
        print(f"Error sending status change email: {e}")
    
    return redirect('admin_dashboard')

@never_cache
def logout(request):
    request.session.flush()
    return redirect('index')

@never_cache
def change_password(request):
    if not request.session.get('alumni_id') or request.session.get('is_admin'):
        return redirect('login')
    
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        alumni = Alumni.objects.get(id=request.session['alumni_id'])
        
        # Verify current password
        if alumni.password != current_password:
            messages.error(request, "Current password is incorrect")
            return redirect('change_password')
        
        # Check if new password is same as current password
        if new_password == current_password:
            messages.error(request, "New password cannot be the same as current password")
            return redirect('change_password')
        
        # Check if new passwords match
        if new_password != confirm_password:
            messages.error(request, "New passwords do not match")
            return redirect('change_password')
        
        # Update password
        alumni.password = new_password
        alumni.save()
        
        messages.success(request, 'Password changed successfully!')
        return redirect('alumni_dashboard')
    
    return render(request, 'alumni_app/change_password.html')

@never_cache
def admin_events(request):
    if not request.session.get('admin_id') or not request.session.get('is_admin'):
        return redirect('login')
    
    admin = Adminn.objects.get(id=request.session.get('admin_id'))
    events = Event.objects.all().order_by('-created_at')
    return render(request, 'alumni_app/admin_events.html', {'events': events})

@never_cache
def create_event(request):
    if not request.session.get('admin_id') or not request.session.get('is_admin'):
        return redirect('login')
    
    admin = Adminn.objects.get(id=request.session.get('admin_id'))
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        date = request.POST.get('date')
        location = request.POST.get('location')
        
        event = Event(
            title=title,
            description=description,
            date=date,
            location=location,
            created_by=admin
        )
        event.save()
        
        # Create notifications for all active alumni
        active_alumni = Alumni.objects.filter(is_active=True)
        for alumni in active_alumni:
            Notification.objects.create(
                alumni=alumni,
                message=f"New event created: {title} on {date}"
            )
        
        messages.success(request, 'Event created successfully!')
        return redirect('admin_events')
    
    return render(request, 'alumni_app/create_event.html')

@never_cache
def edit_event(request, event_id):
    if not request.session.get('admin_id') or not request.session.get('is_admin'):
        return redirect('login')
    
    admin = Adminn.objects.get(id=request.session.get('admin_id'))
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        event.title = request.POST.get('title')
        event.description = request.POST.get('description')
        event.date = request.POST.get('date')
        event.location = request.POST.get('location')
        event.save()
        
        messages.success(request, 'Event updated successfully!')
        return redirect('admin_events')
    
    return render(request, 'alumni_app/edit_event.html', {'event': event})

@never_cache
def delete_event(request, event_id):
    if not request.session.get('admin_id') or not request.session.get('is_admin'):
        return redirect('login')
    
    admin = Adminn.objects.get(id=request.session.get('admin_id'))
    event = get_object_or_404(Event, id=event_id)
    event.delete()
    
    messages.success(request, 'Event deleted successfully!')
    return redirect('admin_events')

@never_cache
def view_events(request):
    if not request.session.get('alumni_id'):
        return redirect('login')
    
    events = Event.objects.filter(is_active=True, date__gte=timezone.now()).order_by('date')
    return render(request, 'alumni_app/view_events.html', {'events': events})

@never_cache
def browse_alumni(request):
    if not request.session.get('alumni_id') or request.session.get('is_admin'):
        return redirect('login')
    
    current_alumni = Alumni.objects.get(id=request.session['alumni_id'])
    
    # Get connected alumni
    connections = Connection.objects.filter(
        models.Q(sender=current_alumni) | models.Q(receiver=current_alumni),
        status='accepted'
    )
    
    connected_alumni = []
    for connection in connections:
        if connection.sender == current_alumni:
            connected_alumni.append(connection.receiver)
        else:
            connected_alumni.append(connection.sender)
    
    # Get connection status and chat room for each alumni
    for alumni in connected_alumni:
        connection = Connection.objects.filter(
            models.Q(sender=current_alumni, receiver=alumni) |
            models.Q(sender=alumni, receiver=current_alumni)
        ).first()
        alumni.connection_status = connection.status if connection else None
        
        # Get or create chat room
        chat_room = ChatRoom.objects.filter(participants=current_alumni).filter(participants=alumni).first()
        if not chat_room:
            chat_room = ChatRoom.objects.create()
            chat_room.participants.add(current_alumni, alumni)
        alumni.chat_room = chat_room
    
    return render(request, 'alumni_app/browse_alumni.html', {'alumni_list': connected_alumni})

@never_cache
def send_connection_request(request, receiver_id):
    if not request.session.get('alumni_id') or request.session.get('is_admin'):
        return redirect('login')
    
    sender = Alumni.objects.get(id=request.session['alumni_id'])
    receiver = get_object_or_404(Alumni, id=receiver_id)
    
    # Check if active connection already exists (pending or accepted)
    if Connection.objects.filter(
        models.Q(sender=sender, receiver=receiver) |
        models.Q(sender=receiver, receiver=sender),
        status__in=['pending', 'accepted']
    ).exists():
        messages.error(request, 'Connection already exists')
        return redirect('browse_alumni')
    
    # Delete any existing rejected connection
    Connection.objects.filter(
        models.Q(sender=sender, receiver=receiver) |
        models.Q(sender=receiver, receiver=sender),
        status='rejected'
    ).delete()
    
    # Create connection request
    connection = Connection.objects.create(sender=sender, receiver=receiver)
    
    # Create notification for receiver
    Notification.objects.create(
        alumni=receiver,
        message=f"{sender.first_name} {sender.last_name} sent you a connection request"
    )
    
    messages.success(request, 'Connection request sent successfully')
    return redirect('browse_alumni')

@never_cache
def respond_connection_request(request, connection_id, action):
    if not request.session.get('alumni_id') or request.session.get('is_admin'):
        return redirect('login')
    
    connection = get_object_or_404(Connection, id=connection_id, receiver_id=request.session['alumni_id'])
    
    if action == 'accept':
        connection.status = 'accepted'
        # Create notification for sender
        Notification.objects.create(
            alumni=connection.sender,
            message=f"{connection.receiver.first_name} {connection.receiver.last_name} accepted your connection request"
        )
        messages.success(request, 'Connection request accepted')
    else:
        connection.status = 'rejected'
        # Create notification for sender
        Notification.objects.create(
            alumni=connection.sender,
            message=f"{connection.receiver.first_name} {connection.receiver.last_name} rejected your connection request"
        )
        messages.info(request, 'Connection request rejected')
    
    connection.save()
    return redirect('alumni_dashboard')

@never_cache
def create_post(request):
    if not request.session.get('alumni_id') or request.session.get('is_admin'):
        return redirect('login')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        image = request.FILES.get('image')
        alumni = Alumni.objects.get(id=request.session['alumni_id'])
        
        if content:
            post = Post(author=alumni, content=content)
            if image:
                post.image = image
            post.save()
            messages.success(request, 'Post created successfully!')
            return redirect('view_posts')
        else:
            messages.error(request, 'Post content cannot be empty')
    
    return render(request, 'alumni_app/create_post.html')

@never_cache
def edit_post(request, post_id):
    if not request.session.get('alumni_id') or request.session.get('is_admin'):
        return redirect('login')
    
    post = get_object_or_404(Post, id=post_id)
    
    # Check if the user is the author of the post
    if post.author.id != request.session['alumni_id']:
        messages.error(request, 'You can only edit your own posts')
        return redirect('view_posts')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        image = request.FILES.get('image')
        remove_image = request.POST.get('remove_image')
        
        if content:
            post.content = content
            
            if remove_image:
                post.image.delete()
            elif image:
                if post.image:
                    post.image.delete()
                post.image = image
                
            post.save()
            messages.success(request, 'Post updated successfully!')
            return redirect('view_posts')
        else:
            messages.error(request, 'Post content cannot be empty')
    
    return render(request, 'alumni_app/edit_post.html', {'post': post})

@never_cache
def view_posts(request):
    if not request.session.get('alumni_id') or request.session.get('is_admin'):
        return redirect('login')
    
    posts = Post.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'alumni_app/view_posts.html', {'posts': posts})

@never_cache
def delete_post(request, post_id):
    if not request.session.get('alumni_id') or request.session.get('is_admin'):
        return redirect('login')
    
    post = get_object_or_404(Post, id=post_id)
    if post.author.id == request.session['alumni_id']:
        post.is_active = False
        post.save()
        messages.success(request, 'Post deleted successfully!')
    else:
        messages.error(request, 'You can only delete your own posts')
    
    return redirect('view_posts')

@never_cache
def view_alumni_profile(request, alumni_id):
    if not request.session.get('alumni_id') and not request.session.get('admin_id'):
        return redirect('login')
    
    alumni = get_object_or_404(Alumni, id=alumni_id, is_active=True)
    
    # Get connection status if the viewer is an alumni
    if request.session.get('alumni_id'):
        current_alumni = Alumni.objects.get(id=request.session['alumni_id'])
        connection = Connection.objects.filter(
            models.Q(sender=current_alumni, receiver=alumni) |
            models.Q(sender=alumni, receiver=current_alumni)
        ).first()
        alumni.connection_status = connection.status if connection else None
    
    context = {
        'profile_alumni': alumni,
    }
    return render(request, 'alumni_app/alumni_profile.html', context)

@never_cache
def inbox(request):
    if not request.session.get('alumni_id') or request.session.get('is_admin'):
        return redirect('login')
    
    alumni = Alumni.objects.get(id=request.session['alumni_id'])
    # Get all chat rooms where the user is a participant
    chat_rooms = ChatRoom.objects.filter(participants=alumni)
    
    # Get the latest message for each chat room
    chat_list = []
    for room in chat_rooms:
        other_participant = room.participants.exclude(id=alumni.id).first()
        last_message = Message.objects.filter(
            Q(sender=alumni, receiver=other_participant) |
            Q(sender=other_participant, receiver=alumni)
        ).order_by('-timestamp').first()
            
        unread_count = Message.objects.filter(
            sender=other_participant,
            receiver=alumni,
            is_read=False
        ).count()
        
        chat_list.append({
            'room': room,
            'other_participant': other_participant,
            'last_message': last_message,
            'unread_count': unread_count
        })
    
    context = {
        'chat_list': chat_list
    }
    
    # If room parameter is provided, get chat room content
    room_id = request.GET.get('room')
    if room_id:
        try:
            room = ChatRoom.objects.get(id=room_id, participants=alumni)
            other_participant = room.participants.exclude(id=alumni.id).first()
            
            # Mark messages as read
            Message.objects.filter(
                sender=other_participant,
                receiver=alumni,
                is_read=False
            ).update(is_read=True)
            
            # Get messages from the last 5 days
            five_days_ago = timezone.now() - timezone.timedelta(days=5)
            messages = Message.objects.filter(
                Q(sender=alumni, receiver=other_participant) |
                Q(sender=other_participant, receiver=alumni),
                timestamp__gte=five_days_ago
            ).order_by('timestamp')
            
            # Check if this chat was cleared by the current user
            cleared_chat = ClearedChat.objects.filter(alumni=alumni, chat_room=room).first()
            if cleared_chat:
                # Only show messages after the clear timestamp
                messages = messages.filter(timestamp__gt=cleared_chat.cleared_at)
            
            context.update({
                'room': room,
                'other_participant': other_participant,
                'messages': messages,
                'current_user': alumni
            })
        except ChatRoom.DoesNotExist:
            pass
    
    return render(request, 'alumni_app/inbox.html', context)

@never_cache
def chat_room(request, room_id):
    if not request.session.get('alumni_id') or request.session.get('is_admin'):
        return redirect('login')
    
    alumni = Alumni.objects.get(id=request.session['alumni_id'])
    room = get_object_or_404(ChatRoom, id=room_id, participants=alumni)
    other_participant = room.participants.exclude(id=alumni.id).first()
    
    # Mark messages as read
    Message.objects.filter(
        sender=other_participant,
        receiver=alumni,
        is_read=False
    ).update(is_read=True)
    
    # Get messages from the last 5 days
    five_days_ago = timezone.now() - timezone.timedelta(days=5)
    messages = Message.objects.filter(
        Q(sender=alumni, receiver=other_participant) |
        Q(sender=other_participant, receiver=alumni),
        timestamp__gte=five_days_ago
    ).order_by('timestamp')
    
    # Check if this chat was cleared by the current user
    cleared_chat = ClearedChat.objects.filter(alumni=alumni, chat_room=room).first()
    if cleared_chat:
        # Only show messages after the clear timestamp
        messages = messages.filter(timestamp__gt=cleared_chat.cleared_at)
    
    return render(request, 'alumni_app/chat_room.html', {
        'room': room,
        'other_participant': other_participant,
        'messages': messages,
        'current_user': alumni
    })

@never_cache
def send_message(request):
    if not request.session.get('alumni_id') or request.session.get('is_admin'):
        return JsonResponse({'status': 'error', 'message': 'Please login to send messages'})
    
    if request.method == 'POST':
        receiver_id = request.POST.get('receiver_id')
        content = request.POST.get('content')
        
        if not content:
            return JsonResponse({'status': 'error', 'message': 'Message content is required'})
        
        sender = Alumni.objects.get(id=request.session['alumni_id'])
        receiver = get_object_or_404(Alumni, id=receiver_id)
        
        # Check if users are connected
        connection = Connection.objects.filter(
            Q(sender=sender, receiver=receiver) |
            Q(sender=receiver, receiver=sender),
            status='accepted'
        ).first()
        
        if not connection:
            return JsonResponse({'status': 'error', 'message': 'You can only message connected alumni'})
        
        # Get or create chat room
        chat_room = ChatRoom.objects.filter(participants=sender).filter(participants=receiver).first()
        if not chat_room:
            chat_room = ChatRoom.objects.create()
            chat_room.participants.add(sender, receiver)
        
        # Create message
        message = Message.objects.create(
            sender=sender,
            receiver=receiver,
            content=content
        )
        
        
        
        # Update chat room's last message timestamp
        chat_room.last_message = timezone.now()
        chat_room.save()
        
        return JsonResponse({
            'status': 'success',
            'message': {
                'content': message.content,
                'timestamp': message.timestamp.strftime('%H:%M'),
                'is_read': message.is_read
            }
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@never_cache
def start_chat(request, alumni_id):
    if not request.session.get('alumni_id') or request.session.get('is_admin'):
        return redirect('login')
    
    sender = Alumni.objects.get(id=request.session['alumni_id'])
    other_alumni = get_object_or_404(Alumni, id=alumni_id)
    
    # Check if users are connected
    connection = Connection.objects.filter(
        Q(sender=sender, receiver=other_alumni) |
        Q(sender=other_alumni, receiver=sender),
        status='accepted'
    ).first()
    
    if not connection:
        return redirect('inbox')
    
    # Get or create chat room
    chat_room = ChatRoom.objects.filter(participants=sender).filter(participants=other_alumni).first()
    if not chat_room:
        chat_room = ChatRoom.objects.create()
        chat_room.participants.add(sender, other_alumni)
    
    return redirect('chat_room', room_id=chat_room.id)

@never_cache
def clear_chat(request, room_id):
    if not request.session.get('alumni_id') or request.session.get('is_admin'):
        return JsonResponse({'status': 'error', 'message': 'Please login to clear messages'})
    
    if request.method == 'POST':
        alumni = Alumni.objects.get(id=request.session['alumni_id'])
        room = get_object_or_404(ChatRoom, id=room_id, participants=alumni)
        
        # Create or update the cleared chat record
        ClearedChat.objects.update_or_create(
            alumni=alumni,
            chat_room=room,
            defaults={'cleared_at': timezone.now()}
        )
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@never_cache
def edit_profile(request):
    if not request.session.get('alumni_id'):
        return redirect('login')
    
    alumni = get_object_or_404(Alumni, id=request.session['alumni_id'])
    
    if request.method == 'POST':
        # Get form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        graduation_year = request.POST.get('graduation_year')
        degree = request.POST.get('degree')
        profession = request.POST.get('profession')
        company = request.POST.get('company')
        industry = request.POST.get('industry')
        location = request.POST.get('location')
        bio = request.POST.get('bio')
        profile_pic = request.FILES.get('profile_pic')
        
        # Update alumni information
        alumni.first_name = first_name
        alumni.last_name = last_name
        alumni.graduation_year = graduation_year
        alumni.degree = degree
        alumni.profession = profession
        alumni.company = company
        alumni.industry = industry
        alumni.location = location
        alumni.bio = bio
        
        # Update profile picture if a new one is provided
        if profile_pic:
            alumni.profile_pic = profile_pic
        
        alumni.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('view_alumni_profile', alumni_id=alumni.id)
    
    context = {
        'alumni': alumni,
    }
    return render(request, 'alumni_app/edit_profile.html', context)
