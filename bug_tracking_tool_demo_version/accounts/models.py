from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Sum

class CustomUser(AbstractUser):
    is_developer = models.BooleanField(default=False)
    is_tester = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    experience = models.CharField(max_length=100, blank=True)
    workload = models.IntegerField(default=0)
    project = models.CharField(max_length=100, blank=True)
    last_bug_assigned = models.DateTimeField(null=True, blank=True)
    groups = models.ManyToManyField('auth.Group', related_name='customuser_set', blank=True, verbose_name='groups', help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.')
    user_permissions = models.ManyToManyField('auth.Permission', related_name='customuser_set', blank=True, verbose_name='user permissions', help_text='Specific permissions for this user.')

    def update_workload(self, effort):
        # Calculate the total effort of bugs assigned to the developer
        total_effort = Bug.objects.filter(assigned_to=self).aggregate(total_effort=Sum('effort'))['total_effort']
        if total_effort is None:
            total_effort = 0
        self.workload = total_effort
        self.save()
    
    def decrease_workload(self, effort):
        # Get the total effort of bugs assigned to the developer
        total_effort = Bug.objects.filter(assigned_to=self).aggregate(total_effort=Sum('effort'))['total_effort']
        print(total_effort)
        print('inside decrease')
        # Check if total_effort is None and set it to 0 if so
        if total_effort is None:
            total_effort = 0
        
        # Subtract the effort from the total_effort
        total_effort -= effort
        
        # Ensure total_effort is non-negative
        total_effort = max(total_effort, 0)
        
        # Update the workload field with the adjusted total_effort
        self.workload = total_effort
        self.save()
    def decrease_workload_unassign(self, effort):
        # Get the total effort of bugs assigned to the developer
        total_effort = Bug.objects.filter(assigned_to=self).aggregate(total_effort=Sum('effort'))['total_effort']
        print(total_effort)
        print('inside decrease')
        # Check if total_effort is None and set it to 0 if so
        if total_effort is None:
            total_effort = 0

        # Ensure total_effort is non-negative
        total_effort = max(total_effort, 0)
        
        # Update the workload field with the adjusted total_effort
        self.workload = total_effort
        self.save()

class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null = True)
    message = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return self.message

class Bug(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Testing', 'Testing'),
        ('Closed', 'Closed'),
        ('Held', 'Held'),
        ('Possibly Duplicate','Possibly Duplicate'),
        ('Duplicate','Duplicate'),
    ]
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ]
    PROJECT_CHOICES = [
        ('Electronic Purchase App', 'Electronic Purchase App'),
        ('E-Reader App', 'E-Reader App'),
        ('Resume Builder', 'Resume Builder'),
        ('Video Editor', 'Video Editor'),
        ('Hold Account', 'Hold Account'),
    ]
    NATURE_CHOICES = [
        ('UI/UX', 'UI/UX'),
        ('Browser', 'Browser'),
        ('Internet', 'Internet'),
        ('Performance', 'Performance'),
        ('Crashing', 'Crashing'),
        ('Not Sure', 'Not Sure'),
    ]
    title = models.CharField(max_length=100)
    description = models.TextField()
    similar_bugs = models.ManyToManyField('self', symmetrical=False, blank=True)  # Many-to-many relationship to itself
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    assigned_to = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='assigned_to',  # Custom related_name for assigned_to field
        null = True
    )
   # check automated priority assignment with below dataset for priority
   # assigned_to automated using Çarkacıoğlu, Levent (2022), “Dataset on Eclipse Bug Records on Bugzilla”, Mendeley Data, V1, doi: 10.17632/t6d9y7yt54.1
    nature_of_bug = models.CharField(max_length=20, choices=NATURE_CHOICES)
    expected_result = models.TextField()
    actual_result = models.TextField()
    frequency = models.IntegerField()
    project = models.CharField(max_length=100, choices=PROJECT_CHOICES)
    raised_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='raised_by'  # Custom related_name for raised_by field
    )
    steps_followed = models.TextField()
    always_sometimes = models.CharField(max_length=20, choices=[('Always', 'Always'), ('Sometimes', 'Sometimes')])
    browser = models.CharField(max_length=100)
    os = models.CharField(max_length=100)
    images_log_files = models.ImageField(upload_to='bug_files/', null=True, blank=True)
    additional_information = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    effort = models.FloatField(default=0, null=True, blank=True)

        
    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        if self.pk:  # Check if the bug already exists (i.e., it's being updated)
            # Get the original bug object from the database
            original_bug = Bug.objects.get(pk=self.pk)
            # Check if the status is being changed to closed or duplicate
            print(original_bug.status)
            if self.status in ['Closed', 'Duplicate']:
                # Subtract the effort from the workload of the assigned developer
                print('inside')
                if self.assigned_to:
                    print('there')
                    self.assigned_to.decrease_workload(self.effort)
                    print(self.assigned_to.workload)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def assign_bug(self):
        # Find all developers who are not overloaded and experienced in handling this type of bug
        eligible_developers = CustomUser.objects.filter(
            is_developer=True,
            project=self.project,
        ).annotate(
            current_workload=Sum('workload')
        ).filter(
            experience__contains=self.nature_of_bug,
        ).order_by('last_bug_assigned')  # Order by the last bug assigned

        # Find the total effort of the bug
        total_effort = self.effort

        assigned_developer = None  # Initialize assigned developer

        if eligible_developers:
            # Iterate through the list of eligible developers
            for developer in eligible_developers:
                # Check if the developer's workload plus bug effort exceeds 40 hours
                if developer.current_workload + total_effort <= 40:
                    # Assign the bug to the selected developer
                    self.assigned_to = developer
                    self.save()
                    developer.update_workload(total_effort)  # Update workload of assigned developer
                    # Update the last_bug_assigned field for the assigned developer
                    developer.last_bug_assigned = timezone.now()
                    developer.save()
                    assigned_developer = developer
                    return  # Exit the loop after assigning the bug
                else:
                    # Set assigned_developer to the first eligible developer if not already set
                    if assigned_developer is None:
                        assigned_developer = CustomUser.objects.get(username='Hold')
        else:
            assigned_developer = CustomUser.objects.get(username='Hold')

        # If no suitable developer is found within the loop, assign the bug to the first eligible developer
        if assigned_developer:
            self.assigned_to = assigned_developer
            self.save()
            assigned_developer.update_workload(total_effort)  # Update workload of assigned developer
            # Update the last_bug_assigned field for the assigned developer
            assigned_developer.last_bug_assigned = timezone.now()
            assigned_developer.save()

    
class BugComment(models.Model):
    bug = models.ForeignKey(Bug, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField(null=True)
    image = models.ImageField(upload_to='comment_images/', null=True, blank=True)
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.author.username} on {self.bug.title}'