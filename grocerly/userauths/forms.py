from django import forms
from django.contrib.auth.forms import UserCreationForm
from userauths.models import User, Profile

class UserRegisterForm(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    email = forms.CharField(widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}))


    class Meta:
        model = User
        fields = ['email', 'username']


class ProfileForm(forms.ModelForm):
    full_name = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "Full Name"}), required=False)
    bio = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "Bio"}), required=False)
    phone = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "Phone"}), required=False)

    class Meta:
        model = Profile
        fields = ['full_name', 'image', 'bio', 'phone']
