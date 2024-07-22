# conftest.py

import pytest
from django.urls import reverse
from django.utils import timezone
from .models import Bug, Notification, BugComment
from accounts.models import CustomUser as User

@pytest.fixture
def user():
    return User.objects.create_user(username='testuser', password='testpassword')

@pytest.fixture
def developer():
    return User.objects.create_user(username='developer', email='developer@example.com', password='password', is_developer=True)

@pytest.fixture
def tester():
    return User.objects.create_user(username='tester', email='tester@example.com', password='password', is_tester=True)

@pytest.fixture
def user_assign_auto():
    return User.objects.create_user(username='Assign-Automatically', password='password', is_developer=True)

@pytest.fixture
def user1():
    return User.objects.create_user(username='developer1', password='password', is_developer=True)

@pytest.fixture
def user2():
    return User.objects.create_user(username='developer2', password='password', is_developer=True)

@pytest.fixture
def user3():
    return User.objects.create_user(username='developer3', password='password', is_developer=True)

@pytest.fixture
def user_hold():
    return User.objects.create_user(username='Hold', password='password', is_developer=True)

@pytest.fixture
def notification(developer):
    return Notification.objects.create(user=developer, message='Test notification')

@pytest.fixture
def bug(user):
    return Bug.objects.create(
        title='Test Bug',
        description='This is a test bug',
        status='Open',
        priority='Low',
        nature_of_bug='UI/UX',
        expected_result='Expected result',
        actual_result='Actual result',
        frequency=1,
        assigned_to=user,
        project='Test Project',
        raised_by=user,
        steps_followed='Test steps',
        always_sometimes='Always',
        browser='Chrome',
        os='Windows',
        additional_information='Additional info',
        effort=1.0,
    )

@pytest.fixture
def bug1(user_assign_auto, user):
    return Bug.objects.create(
        title='Test Bug',
        description='This is a test bug',
        status='Open',
        priority='Low',
        nature_of_bug='UI/UX',
        expected_result='Expected result',
        actual_result='Actual result',
        frequency=1,
        assigned_to=user_assign_auto,
        project='Test Project',
        raised_by=user,
        steps_followed='Test steps',
        always_sometimes='Always',
        browser='Chrome',
        os='Windows',
        additional_information='Additional info',
        effort=1.0,
    )

@pytest.fixture
def bug_comment(bug, user):
    return BugComment.objects.create(
        bug=bug,
        text='Test comment',
        author=user,
        created_at=timezone.now(),
    )
