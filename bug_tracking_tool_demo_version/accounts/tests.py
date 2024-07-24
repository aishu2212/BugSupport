# test_views.py

import pytest
from django.urls import reverse
from django.test import Client
from .models import Bug, Notification, BugComment
from accounts.models import CustomUser as User
from .views import notifications

@pytest.mark.django_db
def test_notifications_view(client, developer, notification):
    client.login(username='developer', password='password')
    response = client.get(reverse('notifications'))
    assert response.status_code == 200
    assert 'Test notification' in response.content.decode()

@pytest.mark.django_db
def test_create_developer_view(client, developer):
    client.login(username='developer', password='password')
    response = client.get(reverse('user_dashboard'))
    assert response.status_code == 200

@pytest.mark.django_db
def test_create_wrong_login_view(client):
    client.login(username='developer2', password='password1')
    response = client.get(reverse('user_login'))
    assert response.status_code == 200

@pytest.mark.django_db
def test_user_signup_view(client):
    response = client.get(reverse('user_signup'))
    assert response.status_code == 200

@pytest.mark.django_db
def test_user_login_view(client):
    response = client.get(reverse('user_login'))
    assert response.status_code == 200

@pytest.mark.django_db
def test_user_dashboard_view(client, developer):
    client.login(username='developer', password='password')
    response = client.get(reverse('user_dashboard'))
    assert response.status_code == 200

@pytest.mark.django_db
def test_profile_view(client, developer):
    client.login(username='developer', password='password')
    response = client.get(reverse('user_dashboard'))
    assert response.status_code == 200

@pytest.mark.django_db
def test_custom_logout_view(client):
    response = client.get(reverse('logout'))
    assert response.status_code == 302

@pytest.mark.django_db
def test_bug_dashboard_view(client, developer):
    client.login(username='developer', password='password')
    response = client.get(reverse('bug_dashboard'))
    assert response.status_code == 200

@pytest.mark.django_db
def test_bug_create_view(client, bug, user):
    client.login(username='aishwarya', password='Aishu@2212')
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
        'raised_by': user.id,
        'assigned_to': user.id,
        'steps_followed': 'Steps followed to reproduce the bug',
        'always_sometimes': 'Always',
        'browser': 'Chrome',
        'os': 'Windows 10',
        'additional_information': 'Additional information about the bug',
        'effort': 3.5
    }
    response = client.post(reverse('bug_create'), data)
    client.post(reverse('bug_create'), data)
    assert response.status_code == 302
    assert Bug.objects.filter(title='Test Bug').exists()




@pytest.mark.django_db
def test_bug_detail_get(client, bug, bug_comment):
    client.login(username='testuser', password='testpassword')
    response = client.get(reverse('bug_detail', kwargs={'bug_id': bug.id}))
    assert response.status_code == 200
    assert 'Test Bug' in response.content.decode()
    assert 'This is a test bug' in response.content.decode()
    assert 'Test comment' in response.content.decode()

@pytest.mark.django_db
def test_bug_detail_post(client, bug, user1, user_assign_auto):
    client.login(username='testuser', password='testpassword')
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
        'raised_by': user1.id,
        'assigned_to': user1.id,
        'steps_followed': 'Steps followed to reproduce the bug',
        'always_sometimes': 'Always',
        'browser': 'Chrome',
        'os': 'Windows 10',
        'additional_information': 'Additional information about the bug',
        'effort': 3.5,
        'comment': 'Checking here'
    }
    response = client.post(reverse('bug_detail', kwargs={'bug_id': bug.id}), updated_data)
    client.post(reverse('bug_detail', kwargs={'bug_id': bug.id}), updated_data)
    assert response.status_code == 302

    updated_bug = Bug.objects.get(id=bug.id)
    assert updated_bug.title == 'Updated Bug Title'
    assert updated_bug.description == 'Updated description'


@pytest.mark.django_db
def test_assign_bug_no_eligible_developers(user_assign_auto, user1, user2, user3, user_hold, bug):
    User.objects.all().update(workload=40)
    bug.assign_bug()
    assert bug.assigned_to == user_hold
    User.objects.all().update(workload=10)
