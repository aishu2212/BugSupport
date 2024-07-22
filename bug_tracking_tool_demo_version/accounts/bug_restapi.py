from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404
from .models import Bug, Notification
from accounts.models import CustomUser
from django.contrib.auth import get_user_model
from django.db.models import Count
from datetime import datetime


class BugDetailView(View):
    def get(self, request, bug_id):
        try:
            bug = Bug.objects.get(pk=bug_id)
            bug_data = {
                'id': bug.id,
                'title': bug.title,
                'description': bug.description,
                'status': bug.status,
                'priority': bug.priority,
                'assigned_to': bug.assigned_to.username if bug.assigned_to else None,
                'nature_of_bug': bug.nature_of_bug,
                'expected_result': bug.expected_result,
                'actual_result': bug.actual_result,
                'frequency': bug.frequency,
                'project': bug.project,
                'raised_by': bug.raised_by.username,
                'steps_followed': bug.steps_followed,
                'always_sometimes': bug.always_sometimes,
                'browser': bug.browser,
                'os': bug.os,
                'additional_information': bug.additional_information,
                'created_at': bug.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': bug.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                'effort': bug.effort
            }
            return JsonResponse({'bug': bug_data})
        except Bug.DoesNotExist:
            return JsonResponse({'error': 'Bug not found'}, status=404)

class FetchUserDetailsView(View):
    def get(self, request, user_id):
        try:
            user = CustomUser.objects.get(pk=user_id)
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_developer': user.is_developer,
                'is_tester': user.is_tester,
                'is_admin': user.is_admin,
                'experience': user.experience,
                'workload': user.workload,
                'project': user.project
            }
            return JsonResponse({'user': user_data})
        except CustomUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        


class NotificationDetailView(View):
    def get(self, request, user_id):
        try:
            # Retrieve the user
            user = get_user_model().objects.get(pk=user_id)
            
            # Retrieve notifications for the user
            notifications = Notification.objects.filter(user=user)
            
            # Serialize the notifications data
            notifications_data = [
                {
                    'id': notification.id,
                    'user_id': notification.user_id,
                    'message': notification.message,
                    'timestamp': notification.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'read': notification.read,
                }
                for notification in notifications
            ]
            
            return JsonResponse({'notifications': notifications_data})
        except get_user_model().DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        
class SimilarBugView(View):
    def get(self, request, bug_id):
        bug = Bug.objects.get(id=bug_id)
        similar_bugs = bug.similar_bugs.all()  # Accessing the related bugs using the similar_bugs field
        similar_bugs_data = [{'id': bug.id, 'title': bug.title} for bug in similar_bugs]
        return JsonResponse({'similar_bugs': similar_bugs_data})

class BugAnalyticsView(View):
    def get(self, request, user_id):
        # Query to get bug count per priority
        total_bugs = Bug.objects.count()

        # Get filters from the request
        project_filter = request.GET.get('project')
        severity_filter = request.GET.get('priority')
        nature_of_bug_filter = request.GET.get('nature_of_bug')
        filter_option = request.GET.get('bug_filter')

        # Get user based on user ID
        try:
            logged_in_user = CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

        # Initialize querysets for raised and assigned bugs
        raised_bugs_queryset = Bug.objects.filter(raised_by=logged_in_user)
        assigned_bugs_queryset = Bug.objects.filter(assigned_to=logged_in_user)

        # Select queryset based on filter option
        if filter_option == 'raised_by':
            bug_queryset = raised_bugs_queryset
        elif filter_option == 'assigned_to':
            bug_queryset = assigned_bugs_queryset
        else:
            bug_queryset = Bug.objects.all()

        # Get bug priority counts
        bug_priority_counts = bug_queryset.values('priority').annotate(count=Count('id'))
        bug_priority_labels = [entry['priority'] for entry in bug_priority_counts]
        bug_priority_data = [entry['count'] for entry in bug_priority_counts]

        # Get bug status counts
        bug_status_counts = bug_queryset.values('status').annotate(count=Count('id'))
        bug_status_labels = [entry['status'] for entry in bug_status_counts]
        bug_status_data = [entry['count'] for entry in bug_status_counts]

        # Get bug project counts
        project_counts = bug_queryset.values('project').annotate(count=Count('id'))
        project_labels = [item['project'] for item in project_counts]
        project_data = [item['count'] for item in project_counts]

        # Get bug category counts
        category_counts = bug_queryset.values('nature_of_bug').annotate(count=Count('id'))
        category_labels = [item['nature_of_bug'] for item in category_counts]
        category_data = [item['count'] for item in category_counts]

        # Get bug counts for each date within selected month and year
        selected_month = int(request.GET.get('month', datetime.now().month))
        selected_year = int(request.GET.get('year', datetime.now().year))
        start_date = datetime(selected_year, selected_month, 1)
        end_date = start_date.replace(day=28)  # To avoid exceeding month's last day

        bug_counts_queryset = bug_queryset.filter(created_at__gte=start_date, created_at__lte=end_date)

        # Apply additional filters if provided
        if project_filter:
            bug_counts_queryset = bug_counts_queryset.filter(project=project_filter)
        if severity_filter:
            bug_counts_queryset = bug_counts_queryset.filter(priority=severity_filter)
        if nature_of_bug_filter:
            bug_counts_queryset = bug_counts_queryset.filter(nature_of_bug=nature_of_bug_filter)

        # Get bug counts for each date
        bug_counts = bug_counts_queryset.values('created_at__date').annotate(count=Count('id'))
        date_labels = [item['created_at__date'].strftime('%Y-%m-%d') for item in bug_counts]
        bug_counts_data = [item['count'] for item in bug_counts]

        context = {
            'total_bugs': total_bugs,
            'bug_priority_labels': bug_priority_labels,
            'bug_priority_data': bug_priority_data,
            'bug_status_labels': bug_status_labels,
            'bug_status_data': bug_status_data,
            'project_labels': project_labels,
            'project_data': project_data,
            'category_labels': category_labels,
            'category_data': category_data,
            'date_labels': date_labels,
            'bug_counts': bug_counts_data,
        }

        return JsonResponse(context)
    
class BugFilterView(View):
    def get(self, request, user_id=None):
        # Get filters from the request
        status_filter = request.GET.get('status')
        priority_filter = request.GET.get('priority')
        project_filter = request.GET.get('project')
        nature_of_bug_filter = request.GET.get('nature_of_bug')

        # If user_id is provided in URL, use it, otherwise default to 1
        if user_id is not None:
            logged_in_user_id = user_id
        else:
            logged_in_user_id = 1  # Default user ID

        # Start with all bugs
        bug_queryset = Bug.objects.all()

        # Filter bugs based on user ID
        bug_queryset = bug_queryset.filter(raised_by_id=logged_in_user_id) | bug_queryset.filter(assigned_to_id=logged_in_user_id)

        # Apply additional filters if provided
        if status_filter:
            bug_queryset = bug_queryset.filter(status=status_filter)
        if priority_filter:
            bug_queryset = bug_queryset.filter(priority=priority_filter)
        if project_filter:
            bug_queryset = bug_queryset.filter(project=project_filter)
        if nature_of_bug_filter:
            bug_queryset = bug_queryset.filter(nature_of_bug=nature_of_bug_filter)

        # Serialize bug queryset into JSON response
        bugs_data = list(bug_queryset.values())
        return JsonResponse({'bugs': bugs_data})