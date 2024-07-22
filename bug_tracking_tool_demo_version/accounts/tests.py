from django.test import TestCase, RequestFactory
from django.urls import reverse
from .models import Bug, Notification
from .views import notifications, mark_notifications_as_read
from accounts.models import CustomUser as User
from .models import Notification, Bug, BugComment
from django.test import TestCase, Client
from django.utils import timezone
from .views import (
    notifications,
    create_developer,
    create_tester,
    user_signup,
    user_login,
    similar_bug_popup,
    bug_create,
    user_dashboard,
    profile_view,
    CustomLogoutView,
    bug_detail,
    mark_notifications_as_read,
    fetch_new_notifications,
    bug_dashboard,
    export_bug_details_to_pdf,
    bug_analytics,
)


class ViewsTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        # Create test users
        self.developer = User.objects.create_user(username='developer', email='developer@example.com', password='password', is_developer = True)
        self.tester = User.objects.create_user(username='tester', email='tester@example.com', password='password', is_tester = True)
        self.user_hold = User.objects.create_user(username='Hold', password='password',is_developer=True)

    def test_notifications_view(self):
        # Create a notification for the developer
        Notification.objects.create(user=self.developer, message="Test notification")
        
        # Log in as developer
        self.client.login(username='developer', password='password')

        # Test notifications view
        response = self.client.get(reverse('notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test notification", str(response.content))


    def test_create_developer_view(self):
        # Log in as admin or authorized user
        self.client.login(username='developer', password='password')
        
        # Test create_developer view
        response = self.client.get(reverse('user_dashboard'))
        self.assertEqual(response.status_code, 200) 

    def test_create_wrong_login_view(self):
        # Log in as admin or authorized user
        self.client.login(username='developer2', password='password1')
        
        # Test create_tester view
        response = self.client.get(reverse('user_login'))
        self.assertEqual(response.status_code, 200)  

    def test_user_signup_view(self):
        # Test user_signup view
        response = self.client.get(reverse('user_signup'))
        self.assertEqual(response.status_code, 200)


    def test_user_login_view(self):
        # Test user_login view
        response = self.client.get(reverse('user_login'))
        self.assertEqual(response.status_code, 200)

    def test_user_dashboard_view(self):
        # Log in as developer
        self.client.login(username='developer', password='password')

        # Test user_dashboard view
        response = self.client.get(reverse('user_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_profile_view(self):
        # Log in as developer
        self.client.login(username='developer', password='password')

        # Test profile_view view
        response = self.client.get(reverse('user_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_custom_logout_view(self):
        # Test CustomLogoutView view
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)


    def test_bug_dashboard_view(self):
        # Log in as developer
        self.client.login(username='developer', password='password')

        # Test bug_dashboard view
        response = self.client.get(reverse('bug_dashboard'))
        self.assertEqual(response.status_code, 200)


class BugCreateViewTestCase(TestCase):
    def setUp(self):
        # Create a user for testing
        self.user = User.objects.create_user(username='aishwarya', password='Aishu@2212', is_developer = True)
        # Create 'assigndev' user
        self.user2 = User.objects.create_user(username='Assign-Automatically', password='password')
        self.user_hold = User.objects.create_user(username='Hold', is_developer=True)
    def test_bug_create_view(self):
        # Log in as the test user
        self.client.login(username='aishwarya', password='Aishu@2212')

        # Prepare data for bug creation
        data = {
            'title': 'Test Bug',
            'description': 'This is a test bug description',
            'nature_of_bug': 'UI/UX',
            'expected_result': 'Expected result of the bug',
            'actual_result': 'Actual result of the bug',
            'frequency': 1,
            'priority': 'Low',
            'status': 'Open',
            'text': 'something',
            'project': 'Electronic Purchase App',
            'raised_by': self.user.id,
            'assigned_to': self.user2.id,
            'steps_followed': 'Steps followed to reproduce the bug',
            'always_sometimes': 'Always',
            'browser': 'Chrome',
            'os': 'Windows 10',
            'additional_information': 'Additional information about the bug',
            'effort': 3.5
        }

        # Make a POST request to create the bug
        response = self.client.post(reverse('bug_create'), data)

        # Check if the bug was created successfully (expecting a redirect)
        self.assertEqual(response.status_code, 302)

        # Check if the bug exists in the database
        bug_exists = Bug.objects.filter(title='Test Bug').exists()
        self.assertTrue(bug_exists)

        # Check if a comment related to the bug was created
        comment_exists = BugComment.objects.filter(bug__title='Test Bug').exists()
        self.assertTrue(comment_exists)


class NotificationsViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        # Create test users
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com', password='password')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='password')
        # Create test notifications
        self.notification1 = Notification.objects.create(user=self.user1, message='Test notification 1')
        self.notification2 = Notification.objects.create(user=self.user1, message='Test notification 2', read=True)
        self.notification3 = Notification.objects.create(user=self.user2, message='Test notification 3')

    def test_notifications_view(self):
        # Test that the notifications view returns a 200 status code
        request = self.factory.get(reverse('notifications'))
        request.user = self.user1
        response = notifications(request)
        self.assertEqual(response.status_code, 200)
        # Test that the view displays notifications for the logged-in user
        self.assertContains(response, 'Test notification 1')
        self.assertContains(response, 'Test notification 2')
        self.assertNotContains(response, 'Test notification 3')


class MarkNotificationsAsReadViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        # Create test user
        self.user = User.objects.create_user(username='user', email='user@example.com', password='password')
        # Create test notification
        self.notification = Notification.objects.create(user=self.user, message='Test notification')

    def test_mark_notifications_as_read_view(self):
        # Test that marking notifications as read changes their read status
        request = self.factory.post(reverse('mark_notifications_as_read'))
        response = mark_notifications_as_read(request)
        self.assertEqual(response.status_code, 200)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.read)


class BugDetailViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.bug = Bug.objects.create(
            title='Test Bug',
            description='This is a test bug',
            status='Open',
            priority='Low',
            nature_of_bug='UI/UX',
            expected_result='Expected result',
            actual_result='Actual result',
            frequency=1,
            assigned_to=self.user,
            project='Test Project',
            raised_by=self.user,
            steps_followed='Test steps',
            always_sometimes='Always',
            browser='Chrome',
            os='Windows',
            additional_information='Additional info',
            effort=1.0,
        )
        self.comment = BugComment.objects.create(
            bug=self.bug,
            text='Test comment',
            author=self.user,
            created_at=timezone.now(),
        )

    def test_bug_detail_get(self):
        # Log in the user
        self.client.login(username='testuser', password='testpassword')

        # Send GET request to bug detail page
        response = self.client.get(reverse('bug_detail', kwargs={'bug_id': self.bug.id}))

        # Check if the page renders successfully
        self.assertEqual(response.status_code, 200)

        # Check if bug details are displayed correctly
        self.assertContains(response, 'Test Bug')
        self.assertContains(response, 'This is a test bug')

        # Check if comments are displayed correctly
        self.assertContains(response, 'Test comment')
    
    def test_bug_detail_post(self):
        # Log in the user
        self.client.login(username='testuser', password='testpassword')
        self.user = User.objects.create(username='Assign-Automatically', is_developer=True)
        self.user_hold = User.objects.create(username='Hold', is_developer=True)
        # Send POST request to update bug details
        updated_data = {
            'title': 'Updated Bug Title',
            'description': 'Updated bug description',
            'nature_of_bug': 'UI/UX',
            'expected_result': 'Expected result of the bug',
            'actual_result': 'Actual result of the bug',
            'frequency': 1,
            'priority': 'Low',
            'status': 'Open',
            'text': 'something',
            'project': 'Electronic Purchase App',
            'raised_by': self.user.id,
            'assigned_to': self.user.id,
            'steps_followed': 'Steps followed to reproduce the bug',
            'always_sometimes': 'Always',
            'browser': 'Chrome',
            'os': 'Windows 10',
            'additional_information': 'Additional information about the bug',
            'effort': 3.5,
            'comment': 'Checking here'
        }
        response = self.client.post(reverse('bug_detail', kwargs={'bug_id': self.bug.id}), updated_data)

        # Check if the bug is updated successfully
        self.assertEqual(response.status_code, 302)  # Should redirect after successful update

        updated_bug = Bug.objects.get(id=self.bug.id)

        # Check if bug details are updated correctly
        self.assertEqual(updated_bug.title, 'Updated Bug Title')
        self.assertEqual(updated_bug.description, 'Updated bug description')


class TestBugAssignment(TestCase):
    def setUp(self):
        # Create test users
        self.user_assign_auto = User.objects.create(username='Assign-Automatically', is_developer=True)
        self.user1 = User.objects.create(username='developer1', is_developer=True, project='Electronic Purchase App', experience='UI/UX')
        self.user2 = User.objects.create(username='developer2', is_developer=True, project='Electronic Purchase App', experience='UI/UX')
        self.user3 = User.objects.create(username='developer3', is_developer=True, project='Electronic Purchase App', experience='UI/UX')
        self.user_hold = User.objects.create(username='Hold', is_developer=True)

        
        # Create a test bug
        self.bug = Bug.objects.create(
            title='Test Bug',
            description='This is a test bug',
            status='Open',
            priority='Low',
            nature_of_bug='UI/UX',
            expected_result='Expected result',
            actual_result='Actual result',
            frequency=1,
            assigned_to=self.user_assign_auto,
            project='Electronic Purchase App',
            raised_by=self.user_assign_auto,
            steps_followed='Test steps',
            always_sometimes='Always',
            browser='Chrome',
            os='Windows',
            additional_information='Additional info',
            effort=1.0,
        )
        
    def test_assign_bug_round_robin(self):
        # Ensure bug is assigned to the first eligible developer
        self.bug.assign_bug()
        self.assertEqual(self.bug.assigned_to, self.user1)
        
        # Ensure workload of assigned developer is updated
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.workload, 1)
        
        # Ensure last_bug_assigned field is updated for the assigned developer
        self.assertIsNotNone(self.user1.last_bug_assigned)
        
        # Reassign bug to check round-robin allocation
        self.bug.assigned_to = self.user_assign_auto
        self.bug.assign_bug()
        self.assertEqual(self.bug.assigned_to, self.user2)
        
        # Reassign bug again
        self.bug.assigned_to = self.user_assign_auto
        self.bug.assign_bug()
        self.assertEqual(self.bug.assigned_to, self.user3)
        
        # Reassign bug again
        self.bug.assigned_to = self.user_assign_auto
        self.bug.assign_bug()
        self.assertEqual(self.bug.assigned_to, self.user1)
        
    def test_assign_bug_no_eligible_developers(self):
        # Set workload of all developers to 40 hours
        User.objects.all().update(workload=40)
        
        # Assign bug when there are no eligible developers
        self.bug.assign_bug()
        
        # Ensure bug is assigned to 'Hold' user
        self.bug.refresh_from_db()
        self.assertEqual(self.bug.assigned_to, self.user_hold)
        
        # Reset workload of all developers
        User.objects.all().update(workload=10)


        


