from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .forms import DeveloperCreationForm, TesterCreationForm, UserLoginForm, CustomUserCreationForm, BugForm, BugCommentForm
from django.shortcuts import render, redirect, get_object_or_404
from .models import Bug, BugComment, Notification
from accounts.models import CustomUser as User
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy, reverse
from django.views.generic.base import RedirectView
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.db.models import Count
from datetime import datetime
import joblib
import re  # For regular expressions
import nltk
from nltk.tokenize import word_tokenize  # For tokenization
from nltk.corpus import stopwords  # For stopwords removal
from nltk.stem import WordNetLemmatizer  # For lemmatization
from difflib import SequenceMatcher
from urllib.parse import unquote
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db.models import Q
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# Load the saved vectorizer and classifier
vectorizer = joblib.load('C:\\Users\\Aishwarya\\Documents\\Notif\\BugTool\\bug_tracking_tool_2103_Version\\bug_tracking_tool\\accounts\\vectorizer.pkl')
classifier = joblib.load('C:\\Users\\Aishwarya\\Documents\\Notif\\BugTool\\bug_tracking_tool_2103_Version\\bug_tracking_tool\\accounts\\classifier.pkl')
@login_required
def create_developer(request):
    if request.user.is_staff:
        if request.method == 'POST':
            form = DeveloperCreationForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.is_developer = True
                user.email = form.cleaned_data['email']
                user.save()
                return redirect('user_dashboard')
        else:
            form = DeveloperCreationForm()
        return render(request, 'create_developer.html', {'form': form})
    else:
        pass

@login_required
def create_tester(request):
    if request.user.is_staff:
        if request.method == 'POST':
            form = TesterCreationForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.is_tester = True
                user.email = form.cleaned_data['email']
                user.save()
                return redirect('user_dashboard')
        else:
            form = TesterCreationForm()
        return render(request, 'create_tester.html', {'form': form})
    else:
        pass

def user_signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.email = form.cleaned_data['email']
            login(request, user)
            return redirect('user_login')  
    else:
        form = CustomUserCreationForm()
    return render(request, 'user_signup.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                # Redirect to corresponding dashboard based on user role
                return redirect('user_dashboard')
            else:
                pass  # Handle invalid credentials
    else:
        form = UserLoginForm()
    return render(request, 'user_login.html', {'form': form})

def jaccard_similarity(s1, s2):
    set1 = set(s1.split())
    set2 = set(s2.split())
    intersection = len(set1.intersection(set2))
    union = len(set1) + len(set2) - intersection
    return intersection / union if union != 0 else 0

def levenshtein_similarity(s1, s2):
    return SequenceMatcher(None, s1, s2).ratio()

def get_similar_bugs(new_bug):
    title_similar_threshold = 0.2
    description_similar_threshold = 0.3
    nature_similar_threshold = 1
    similar_bugs = []
    for bug in Bug.objects.all():
        title_similarity = jaccard_similarity(new_bug.title, bug.title)
        description_similarity = levenshtein_similarity(new_bug.description, bug.description)
        nature_similarity = jaccard_similarity(new_bug.nature_of_bug, bug.nature_of_bug)
        
        overall_similarity = (title_similarity + description_similarity + nature_similarity) / 3
        
        if (title_similarity >= title_similar_threshold or
            description_similarity >= description_similar_threshold or
            nature_similarity >= nature_similar_threshold) and overall_similarity > 0.25:
            similar_bugs.append((bug, overall_similarity))
    
    # Sort the similar_bugs list by similarity score in descending order
    similar_bugs.sort(key=lambda x: x[1], reverse=True)
    print(similar_bugs[:5])
    # Return only the top 5 similar bugs
    if len(similar_bugs) > 5:
        return similar_bugs[:5]
    else:
        return similar_bugs

def similar_bug_popup(request):
    similar_bugs_data = []
    similar_bugs_query = request.META.get('QUERY_STRING', '')

    # Split the raw query string by '&' to get individual parameter-value pairs
    parameters = similar_bugs_query.split('&')

    # Iterate over each parameter-value pair
    for parameter in parameters:
        # Check if the parameter starts with 'similar_bugs='
        if parameter.startswith('similar_bugs='):
            # Extract the value part after 'similar_bugs='
            value = parameter[len('similar_bugs='):]

            # Split the value by '&' to get individual bug entries
            bug_entries = value.split('&')

            # Process each bug entry
            for bug_entry in bug_entries:
                # Split the bug entry by ':' to separate title and description
                title, description = bug_entry.split(':')
                title = unquote(title)
                description = unquote(description)
                similar_bugs_data.append({'title': title, 'description': description})

    return render(request, 'similar_bug_popup.html', {'similar_bugs': similar_bugs_data})



def preprocess_text(text):
    stop_words = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()
    # Convert text to lowercase
    text = str(text)
    text = text.lower()
    # Remove special characters and digits
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    # Tokenize the text
    tokens = word_tokenize(text)
    # Remove stopwords and lemmatize tokens
    tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words]
    # Join tokens back into a string
    preprocessed_text = ' '.join(tokens)
    return preprocessed_text

@login_required
def bug_create(request):
    if request.method == 'POST':
        raised_by_username = request.user.username
        raised_by_user = get_user_model().objects.get(username=raised_by_username)
        form = BugForm(request.POST, request.FILES, user=request.user)
        comment_form = BugCommentForm(request.POST, request.FILES)  # Add comment form
        
        form.instance.raised_by = raised_by_user  # Assigning user to form instance
        if form.is_valid() and comment_form.is_valid():
            bug = form.save(commit=False)
            similar_bugs = get_similar_bugs(bug)
            autoassign_username = 'Assign-Automatically'
            certain_user = User.objects.get(username=autoassign_username)
            if bug.assigned_to != None:
                print('atleast here')
                if bug.assigned_to == certain_user:
                    print('here assigning........')
                    bug.assign_bug()
                else:
                    bug.save()
                    # Manually assigned bug, update developer's workload
                    bug.assigned_to.update_workload(bug.effort)
            if not (request.user.is_staff or request.user.is_developer or request.user.is_tester):
                description = preprocess_text(bug.description)  # Preprocess the text
                description_tfidf = vectorizer.transform([description])  # Vectorize the text
                # Check if specific keywords are present in the description
                specific_keywords = ['add', 'change', 'better', 'improve', 'enhance', 'changed', 'added', 'improved', 'modified', 'enhanced']
                keywords_present = any(keyword in description for keyword in specific_keywords)

                # Predict bug priority using the loaded classifier
                predicted_priority = classifier.predict(description_tfidf)[0]
            
                if predicted_priority == 'enhancement':
                    if keywords_present:
                        bug.priority = 'Low'
                        bug.effort = 4
                    else:
                        bug.priority = 'Medium'
                        bug.effort = 8
                elif predicted_priority == 'major':
                    bug.priority = 'High'
                    bug.effort = 10
                else:
                    bug.priority = 'Medium'  # Assign the predicted priority
                    bug.effort = 8
                bug.save()
                print('Effort',bug.effort)
                bug.assign_bug()
            print(similar_bugs)
            
            if similar_bugs:
                bug.status = "Possibly Duplicate"
                similar_bug_ids = [bug[0].id for bug in similar_bugs]  # Extracting IDs of similar bugs
                bug.save()
                bug.similar_bugs.set(similar_bug_ids)
            
                similar_bug_titles_descriptions = Bug.objects.filter(id__in=similar_bug_ids).values_list('title', 'description')
                # Construct a query string with both titles and descriptions
                query_string = '&'.join([f'similar_bugs={title}:{description}' for title, description in similar_bug_titles_descriptions])


            bug.save()  # Save the bug object first to generate an ID

            # Save comment
            comment = comment_form.save(commit=False)
            comment.bug = bug
            comment.author = request.user
            comment.save()
            
            # Trigger notification to assigned to and raised by users
            assigned_to = form.cleaned_data.get('assigned_to')
            assigned_to_user = assigned_to if assigned_to else None
            raised_by_user = bug.raised_by
            message = f"A new bug ({bug.title}) has been created."
            user_ids = set()
            if assigned_to_user:
                user_ids.add(assigned_to_user.id)
            user_ids.add(raised_by_user.id)
            if user_ids:
                send_notification_to_users(bug.id, user_ids, message)
                send_bug_create_email(bug, user_ids)
            if similar_bugs:
                return redirect(reverse('similar_bug_popup') + '?' + query_string)
            return redirect('user_profile')
        else:
            print(form.errors)
            print(comment_form.errors)
            filtered_users = get_filtered_users()
            return render(request, 'bug_create.html', {'form': form, 'comment_form': comment_form, 'filtered_users': filtered_users})
    else:
        form = BugForm(user=request.user)
        comment_form = BugCommentForm()  # Initialize comment form
        filtered_users = get_filtered_users()
        return render(request, 'bug_create.html', {'form': form, 'comment_form': comment_form, 'filtered_users': filtered_users})


def get_filtered_users():
    return (
        get_user_model().objects.filter(is_staff=True) |
        get_user_model().objects.filter(is_developer=True) |
        get_user_model().objects.filter(is_tester=True)
    )

@login_required
def user_dashboard(request):
    return render(request, 'user_dashboard.html')


@login_required
def profile_view(request):
    raised_bugs = Bug.objects.filter(raised_by=request.user)
    assigned_bugs = Bug.objects.filter(assigned_to=request.user)
    
    # Define Q objects for filtering raised bugs
    raised_filter_queries = []

    # Handle search and filter parameters for raised bugs
    raised_search_query = request.GET.get('raised_search_query')
    raised_status_filter = request.GET.get('raised_status')
    raised_priority_filter = request.GET.get('raised_priority')
    raised_project_filter = request.GET.get('raised_project')  # New filter for project
    raised_nature_of_bug_filter = request.GET.get('raised_nature_of_bug')  # New filter for nature of bug
    created_from_filter = request.GET.get('created_from')
    updated_from_filter = request.GET.get('updated_from')
    
    # Handle search query for raised bugs
    if raised_search_query:
        raised_filter_queries.append(Q(title__icontains=raised_search_query))

    # Handle status filter for raised bugs
    if raised_status_filter:
        raised_filter_queries.append(Q(status=raised_status_filter))

    # Handle priority filter for raised bugs
    if raised_priority_filter:
        raised_filter_queries.append(Q(priority=raised_priority_filter))
        
    # Handle created_from filter for raised bugs
    if created_from_filter:
        raised_filter_queries.append(Q(created_at__date__gte=created_from_filter))
    
    # Handle updated_from filter for raised bugs
    if updated_from_filter:
        raised_filter_queries.append(Q(updated_at__date__gte=updated_from_filter))

    # Handle project filter for raised bugs
    if raised_project_filter:
        raised_filter_queries.append(Q(project=raised_project_filter))
    
    # Handle nature of bug filter for raised bugs
    if raised_nature_of_bug_filter:
        raised_filter_queries.append(Q(nature_of_bug=raised_nature_of_bug_filter))
    
    # Apply filters for raised bugs
    if raised_filter_queries:
        raised_bugs = raised_bugs.filter(*raised_filter_queries)

    # Define Q objects for filtering assigned bugs
    assigned_filter_queries = []

    # Handle search and filter parameters for assigned bugs
    assigned_search_query = request.GET.get('assigned_search_query')
    assigned_status_filter = request.GET.get('assigned_status')
    assigned_priority_filter = request.GET.get('assigned_priority')
    assigned_created_from_filter = request.GET.get('assigned_created_from')
    assigned_updated_from_filter = request.GET.get('assigned_updated_from')
    assigned_project_filter = request.GET.get('assigned_project')  # New filter for project
    assigned_nature_of_bug_filter = request.GET.get('assigned_nature_of_bug')  # New filter for nature of bug
    
    # Handle search query for assigned bugs
    if assigned_search_query:
        assigned_filter_queries.append(Q(title__icontains=assigned_search_query))

    # Handle status filter for assigned bugs
    if assigned_status_filter:
        assigned_filter_queries.append(Q(status=assigned_status_filter))

    # Handle priority filter for assigned bugs
    if assigned_priority_filter:
        assigned_filter_queries.append(Q(priority=assigned_priority_filter))
    
    # Handle project filter for assigned bugs
    if assigned_project_filter:
        assigned_filter_queries.append(Q(project=assigned_project_filter))
    
    # Handle nature of bug filter for assigned bugs
    if assigned_nature_of_bug_filter:
        assigned_filter_queries.append(Q(nature_of_bug=assigned_nature_of_bug_filter))
        
    # Handle created_from filter for assigned bugs
    if assigned_created_from_filter:
        assigned_filter_queries.append(Q(created_at__date__gte=assigned_created_from_filter))
    
    # Handle updated_from filter for assigned bugs
    if assigned_updated_from_filter:
        assigned_filter_queries.append(Q(updated_at__date__gte=assigned_updated_from_filter))
    
    # Apply filters for assigned bugs
    if assigned_filter_queries:
        assigned_bugs = assigned_bugs.filter(*assigned_filter_queries)

    return render(request, 'user_profile.html', {
        'raised_bugs': raised_bugs,
        'assigned_bugs': assigned_bugs,
    })

class CustomLogoutView(RedirectView):
    url = reverse_lazy('user_login')  # Redirect to the login page after logout

    def get(self, request, *args, **kwargs):
        logout(request)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)
    
User = get_user_model()

def send_notification_to_users(bug_id, user_ids, message):
    user_ids = set(user_ids)
    # Create notification for each user
    for user_id in user_ids:
        user = User.objects.filter(id=user_id).first()
        if user:
            Notification.objects.create(user=user,message=message)

def send_bug_update_email(bug, user_ids):
    subject = 'Bug Updated: {}'.format(bug.id)
    latest_comment = bug.comments.last()  
    
    # Render the email template with bug details and latest comment
    html_message = render_to_string('bug_update_email.html', {'bug': bug, 'latest_comment': latest_comment})

    plain_message = strip_tags(html_message)
    # Sender's email address
    from_email = 'softwarebugupdates@gmail.com'
    to_emails = [user.email for user in User.objects.filter(id__in=user_ids)]
    send_mail(subject, plain_message, from_email, to_emails, html_message=html_message)

def send_bug_create_email(bug, user_ids):
    subject = 'Bug Created: {}'.format(bug.id)
    # Retrieve the latest comment related to the bug
    latest_comment = bug.comments.last() 
    
    # Render the email template with bug details and latest comment
    html_message = render_to_string('bug_create_email.html', {'bug': bug, 'latest_comment': latest_comment})

    plain_message = strip_tags(html_message)
    # Sender's email address
    from_email = 'softwarebugupdates@gmail.com'
    to_emails = [user.email for user in User.objects.filter(id__in=user_ids)]
    send_mail(subject, plain_message, from_email, to_emails, html_message=html_message)
    
def bug_detail(request, bug_id):
    bug = get_object_or_404(Bug, id=bug_id)
    old_assigned_to = bug.assigned_to  # Store the old assigned developer
    old_effort = bug.effort
    print(old_assigned_to.username)
    similar_bugs = bug.similar_bugs.all()
    comments = bug.comments.all()  # Fetch all comments related to the bug
    if request.method == 'POST':
        form = BugForm(request.POST, request.FILES, instance=bug)
        comment_form = BugCommentForm(request.POST, request.FILES)
        
        if form.is_valid() and comment_form.is_valid():
            print(form.instance.assigned_to)
            
            form.instance.images_log_files = bug.images_log_files 
            form.save()
            
            new_image = request.FILES.get('images_log_files')
            if new_image:
                bug.images_log_files = new_image
                bug.save()
            
            comment = comment_form.save(commit=False)
            comment.bug = bug
            comment.author = request.user
            new_comment_image = request.FILES.get('image')
            if new_comment_image:
                comment.image = new_comment_image
            comment.save()

             # Check if the status is being changed to closed or duplicate
            if bug.status in ['Closed', 'Duplicate']:
                # Subtract the effort from the workload of the assigned developer
                if old_assigned_to:
                    old_assigned_to.decrease_workload(bug.effort)
                    bug.effort = 0  # Set effort to 0 as the bug is closed or duplicate
            
            print('Assigned new',bug.assigned_to.username)
            # Check if the assigned developer has changed
            if old_assigned_to != bug.assigned_to:
                # If old_assigned_to is not None, decrease workload
                print('inside old assigned')
                if bug.assigned_to:
                    print(bug.effort)
                    bug.assigned_to.update_workload(bug.effort)
                    print(bug.assigned_to.workload)
                if old_assigned_to:
                    print('old ', old_assigned_to.workload)
                    print(bug.effort)
                    old_assigned_to.decrease_workload_unassign(bug.effort)
                    print('old after decrease',old_assigned_to.workload)
             # Check if the effort field has been modified
            if old_effort != bug.effort:
                # Calculate the difference in effort
                effort_difference = bug.effort - old_effort
                # If bug is assigned to a developer, update their workload
                if bug.assigned_to:
                    if effort_difference >= 0:
                        bug.assigned_to.update_workload(effort_difference)
                    else:
                        bug.assigned_to.decrease_workload(abs(effort_difference))

            
            # Check if bug is assigned to certain user for automatic reassignment
            autoassign_username = 'Assign-Automatically'
            certain_user = User.objects.get(username=autoassign_username)
            if bug.assigned_to.username == certain_user.username:
                bug.assign_bug()
            # Trigger notification after successful update
            user_ids = [bug.assigned_to.id, bug.raised_by.id] if bug.assigned_to and bug.raised_by else []
            if user_ids:
                send_notification_to_users(bug_id, user_ids, 'Bug Updated:'+str(bug_id))
                send_bug_update_email(bug, user_ids)
            return redirect('user_dashboard')
        else:
            print(form.errors)
            print(comment_form.errors)
    else:
        form = BugForm(instance=bug)
        comment_form = BugCommentForm()
    return render(request, 'bug_detail.html', {'form': form, 'bug': bug, 'comments': comments, 'comment_form': comment_form, 'similar_bugs': similar_bugs})



def mark_notifications_as_read(request):
    # Mark all notifications as read
    Notification.objects.all().update(read=True)
    return JsonResponse({'success': True})

def fetch_new_notifications(request):
    # Fetch unread notifications count
    unread_notifications_count = Notification.objects.filter(read=False).count()
    return JsonResponse({'count': unread_notifications_count})

def notifications(request):
    # Get all notifications for the current user
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')

    # Get unread notifications for the current user
    unread_notifications = Notification.objects.filter(user=request.user, read=False).order_by('-timestamp')

    context = {
        'notifications': notifications,
        'unread_notifications': unread_notifications,
    }
    return render(request, 'notifications.html', context)

def notification_count(request):
    # Retrieve the notification count and return as JSON
    notifications = Notification.objects.all()
    unread_notifications_count = notifications.filter(read=False).count()
    return JsonResponse({'count': unread_notifications_count})

def bug_dashboard(request):
    
    bugs = Bug.objects.all()
    assigned_users = User.objects.filter(Q(is_staff=True) | Q(is_developer=True) | Q(is_tester=True))

    # Search
    query = request.GET.get('q')
    if query:
        # Check if the search input is a Bug ID ( Bug ID is an integer field)
        try:
            bug_id = int(query)
            bugs = bugs.filter(id=bug_id)
        except ValueError:
            # If not a Bug ID, perform a general search based on other criteria
            bugs = bugs.filter(
                Q(title__icontains=query) |
                Q(assigned_to__username__icontains=query) |
                Q(description__icontains=query)
            )

    # Filter by status, assigned to, priority, and project
    status_filter = request.GET.get('status')
    if status_filter:
        bugs = bugs.filter(status=status_filter)

    assigned_to_filter = request.GET.get('assigned_to')
    if assigned_to_filter:
        bugs = bugs.filter(assigned_to__username=assigned_to_filter)

    priority_filter = request.GET.get('priority')
    if priority_filter:
        bugs = bugs.filter(priority=priority_filter)

    project_filter = request.GET.get('project')
    if project_filter:
        bugs = bugs.filter(project=project_filter)
    
    created_from_filter = request.GET.get('created_from')
    if created_from_filter:
        bugs = bugs.filter(created_at__date__gte=created_from_filter)

    updated_from_filter = request.GET.get('updated_from')
    if updated_from_filter:
        # Assuming created_from_filter is in the format 'YYYY-MM'
        # year, month = updated_from_filter.split('-')
        # bugs = bugs.filter(updated_at__year=year, updated_at__month=month)
        bugs = bugs.filter(updated_at__date__gte=updated_from_filter)
    
    project_filter = request.GET.get('project')
    if project_filter:
        bugs = bugs.filter(project=project_filter)
        
    nature_of_bug_filter = request.GET.get('nature_of_bug')
    if nature_of_bug_filter:
        bugs = bugs.filter(nature_of_bug=nature_of_bug_filter)

    context = {
        'bugs': bugs,
        'assigned_users': assigned_users,
        'status_filter': status_filter,
        'assigned_to_filter': assigned_to_filter,
        'priority_filter': priority_filter,
        'project_filter': project_filter,
        'project_filter': project_filter,
        'nature_of_bug_filter': nature_of_bug_filter,
        'created_at_filter': created_from_filter, 
        'updated_at_filter': updated_from_filter, 
    }
    return render(request, 'bug_dashboard.html', context)

from xhtml2pdf import pisa

def export_bug_details_to_pdf(request, bug_id):
    # Retrieve bug details from the database based on bug_id
    bug = Bug.objects.get(id=bug_id)

    # Render the bug details template with bug data
    template_path = 'bug_details_pdf.html'
    context = {'bug': bug}
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="bug_{bug_id}.pdf"'

    # Render HTML template
    template = render(request, template_path, context)

    # Create PDF from HTML template
    pisa_status = pisa.CreatePDF(template.content, dest=response)

    # If PDF creation failed, return error response
    if pisa_status.err:
        return HttpResponse('PDF creation failed', status=500)
    
    return response

def bug_analytics(request):
    # Query to get bug count per priority
    total_bugs = Bug.objects.count()
    logged_in_user = request.user

    # Get filters from the request
    project_filter = request.GET.get('project')
    severity_filter = request.GET.get('priority')
    nature_of_bug_filter = request.GET.get('nature_of_bug')
    filter_option = request.GET.get('bug_filter')

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
        'total_bugs': Bug.objects.count(),
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

    return render(request, 'bug_analytics.html', context)