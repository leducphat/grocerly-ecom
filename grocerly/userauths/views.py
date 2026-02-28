from django.shortcuts import redirect, render
from userauths.forms import UserRegisterForm, ProfileForm
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from userauths.models import User, Profile

# User = settings.AUTH_USER_MODEL

# Create your views here.
def register_view(request):

    if request.method == 'POST':
        form = UserRegisterForm(request.POST or None)
        if form.is_valid():
            new_user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Welcome, {username}! Your account has been created successfully!')
            new_user = authenticate(username=form.cleaned_data['email'],
                                    password=form.cleaned_data['password1'])
            login(request, new_user)
            return redirect('core:index')
    else:
        form = UserRegisterForm()


    context = {
        'form': form
    }

    return render(request, 'userauths/sign-up.html', context)

def login_view(request):
    if request.user.is_authenticated:
        messages.warning(request, 'You are already logged in!')
        return redirect('core:index')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back {user.username}!')
                return redirect('core:index')
            else:
                messages.warning(request, 'User does not exist. Please try again.')

        except:
            messages.warning(request, f'User with email {email} does not exist.')
        


    

    context = {

    }

    return render(request, 'userauths/sign-in.html', context)


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('userauths:sign-in')


@login_required
def profile_update(request):
    profile = Profile.objects.get(user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            new_form = form.save(commit=False)
            new_form.user = request.user
            new_form.save()
            messages.success(request, "Profile Updated Successfully.")
            return redirect("core:dashboard")
    else:
        form = ProfileForm(instance=profile)

    context = {
        "form": form,
        "profile": profile,
    }
    return render(request, "userauths/profile-edit.html", context)