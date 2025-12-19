from django.db import models

# Create your models here.


class Alumni(models.Model):
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    graduation_year = models.IntegerField()
    degree = models.CharField(max_length=100)
    profession = models.CharField(max_length=100)
    company = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

class Adminn(models.Model):
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=100)  # Plain text for this example
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_superadmin = models.BooleanField(default=False)

    def __str__(self):
        return self.username
class Notification(models.Model):
    alumni = models.ForeignKey(Alumni, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.alumni.username}"

class Feedback(models.Model):
    alumni = models.ForeignKey(Alumni, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Feedback from {self.alumni.username}"

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=200)
    created_by = models.ForeignKey(Adminn, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Connection(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    sender = models.ForeignKey(Alumni, on_delete=models.CASCADE, related_name='sent_connections')
    receiver = models.ForeignKey(Alumni, on_delete=models.CASCADE, related_name='received_connections')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['sender', 'receiver']

    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username} ({self.status})"

class Post(models.Model):
    author = models.ForeignKey(Alumni, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Post by {self.author.username} - {self.created_at}"

class Message(models.Model):
    sender = models.ForeignKey(Alumni, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(Alumni, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']



class ChatRoom(models.Model):
    participants = models.ManyToManyField(Alumni, related_name='chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    last_message = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_message']

    def __str__(self):
        return f"Chat Room {self.id}"

class ClearedChat(models.Model):
    alumni = models.ForeignKey(Alumni, on_delete=models.CASCADE)
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    cleared_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['alumni', 'chat_room']

    def __str__(self):
        return f"{self.alumni.username} cleared chat {self.chat_room.id}"