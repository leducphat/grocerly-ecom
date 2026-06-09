from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from userauths.models import User, Profile

class UserRegisterForm(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': _('Username')}))
    email = forms.CharField(widget=forms.EmailInput(attrs={'placeholder': _('Email')}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': _('Password')}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': _('Confirm Password')}))


    class Meta:
        model = User
        fields = ['email', 'username']


class ProfileForm(forms.ModelForm):
    full_name = forms.CharField(widget=forms.TextInput(attrs={"placeholder": _("Full Name")}), required=False)
    bio = forms.CharField(widget=forms.TextInput(attrs={"placeholder": _("Bio")}), required=False)
    phone = forms.CharField(widget=forms.TextInput(attrs={"placeholder": _("Phone")}), required=False)

    class Meta:
        model = Profile
        fields = ['full_name', 'image', 'bio', 'phone']
