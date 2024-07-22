from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser,  Bug, BugComment
from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q

class DeveloperCreationForm(UserCreationForm):
    experience = forms.ChoiceField(choices=Bug.NATURE_CHOICES)
    project = forms.ChoiceField(choices=Bug.PROJECT_CHOICES)

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2', 'experience', 'project')

class TesterCreationForm(UserCreationForm):
    experience = forms.ChoiceField(choices=Bug.NATURE_CHOICES)
    project = forms.ChoiceField(choices=Bug.PROJECT_CHOICES)

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2', 'experience', 'project')


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')

class UserLoginForm(AuthenticationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'password')
    
class BugForm(forms.ModelForm):
    class Meta:
        model = Bug
        fields = '__all__'
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  
        super(BugForm, self).__init__(*args, **kwargs)
        self.fields['assigned_to'].required = False
        self.fields['priority'].required = False
        self.fields['status'].required = False
        if user and not (user.is_staff or user.is_developer or user.is_tester):     
            self.fields['assigned_to'].widget = forms.HiddenInput()
            self.fields['priority'].widget = forms.HiddenInput()
            self.fields['status'].widget = forms.HiddenInput()
        else:
            self.fields['assigned_to'].initial = None
            self.fields['priority'].initial = 'Unassigned'
            self.fields['priority'].initial = 'Open'

class BugCommentForm(forms.ModelForm):
    class Meta:
        model = BugComment
        fields = ['text', 'image']