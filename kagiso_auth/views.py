from authomatic import Authomatic
from authomatic.adapters import DjangoAdapter
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.db.utils import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from . import forms
from .exceptions import EmailNotConfirmedError
from .models import KagisoUser
from .utils import get_setting


@never_cache
@csrf_exempt
def sign_up(request):
    confirm_message = (
        'You will receive an email with confirmation instructions shortly. '
        'This link will expire within 24 hours.'
    )
    error_message = 'You already have an account.'
    next = request.GET.get('next', '/')

    if request.user.is_authenticated:
        return HttpResponseRedirect(next)

    oauth_data = request.session.get('oauth_data')

    if request.method == 'POST':
        form = forms.SignUpForm.create(
            post_data=request.POST,
            oauth_data=oauth_data
        )

        if form.is_valid():
            try:
                user = form.save(
                    app_name=get_setting(settings.APP_NAME, request)
                )
            except IntegrityError:
                messages.error(request, error_message)
                return HttpResponseRedirect(reverse('sign_in'))

            # Social sign ins provide emails that have already been confirmed
            # via FB, Google etc...
            if not oauth_data:
                _send_confirmation_email(user, request)
                messages.success(request, confirm_message)
                return HttpResponseRedirect(next)

            _social_login(request, user.email, oauth_data['provider'])
            return HttpResponseRedirect(next)
    else:
        form = forms.SignUpForm.create(oauth_data=oauth_data)

    return render(
        request,
        'kagiso_auth/sign_up.html',
        {
            'form': form,
            'next': next,
        }
    )


def _send_confirmation_email(user, request):
    msg = EmailMessage()
    msg.to = [user.email]
    msg.from_email = get_setting(settings.AUTH_FROM_EMAIL, request)
    msg.subject = 'Confirm Your Account'
    msg.template = get_setting(settings.SIGN_UP_EMAIL_TEMPLATE, request)
    msg.substitution_data = {
        'link': request.build_absolute_uri(reverse('confirm_account')),
        'token': user.confirmation_token,
        'user_id': user.id,
        'first_name': user.first_name,
        'next': request.GET.get('next', '/')
    }
    msg.send()


@never_cache
def confirm_account(request):
    confirm_message = 'We have confirmed your details, please sign in below'

    user_id = request.GET.get('user_id')
    token = request.GET.get('token')
    next = request.GET.get('next', '/')

    redirect = '?next=' + next

    user = get_object_or_404(KagisoUser, id=user_id)
    user.confirm_email(token)

    messages.success(request, confirm_message)

    return HttpResponseRedirect(reverse('sign_in') + redirect)


@never_cache
@csrf_exempt
def sign_in(request):
    next = request.GET.get('next', '/')

    if request.user.is_authenticated:
        return HttpResponseRedirect(next)

    if request.method == 'POST':
        form = forms.SignInForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data['remember_me']
            try:
                user = authenticate(
                    email=email,
                    password=password,
                )

                if user:
                    user.last_sign_in_via = get_setting(
                        settings.APP_NAME,
                        request
                    )
                    user.save()
                    login(request, user)

                    if not remember_me:
                        request.session.set_expiry(0)

                    return HttpResponseRedirect(next)
                else:
                    messages.error(request, 'Incorrect email or password')
            except EmailNotConfirmedError:
                resend_message = (
                    'Please first confirm your email address. '
                    '<a href="/resend_confirmation?email={email}">'
                    'Resend confirmation email</a>'
                ).format(email=email)
                messages.error(
                    request,
                    mark_safe(resend_message)
                )
    else:
        form = forms.SignInForm()

    return render(
        request,
        'kagiso_auth/sign_in.html',
        {
            'form': form,
            'next': next,
        }
    )


@never_cache
@csrf_exempt
def update_details(request):
    confirm_message = 'Your details have been updated successfully.'
    error_message = 'Something went wrong. Please try again.'

    if not request.user.is_authenticated:
        redirect = '?next=/update_details/'
        return HttpResponseRedirect(reverse('sign_in') + redirect)

    user = get_object_or_404(KagisoUser, id=request.user.id)
    form = forms.UpdateDetailsForm({
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'mobile': user.profile['mobile'],
        'gender': user.profile['gender'],
        'region': user.profile['region'],
        'birth_date': user.profile['birth_date'],
        'alerts': user.profile['alerts'],
    })

    if request.method == 'POST':
        oauth_data = request.session.get('oauth_data')
        form = forms.UpdateDetailsForm.create(
            post_data=request.POST,
            oauth_data=oauth_data
        )

        if form.is_valid():
            try:
                user = form.save(
                    app_name=get_setting(settings.APP_NAME, request),
                    user=user
                )
                messages.success(request, confirm_message)
            except IntegrityError:
                messages.error(request, error_message)
                return HttpResponseRedirect(reverse('update_details'))

    return render(
        request,
        'kagiso_auth/update_details.html',
        {
            'form': form
        }
    )


@never_cache
def oauth(request, provider):
    response = HttpResponse()
    authomatic = Authomatic(
        get_setting(settings.AUTHOMATIC_CONFIG, request),
        get_setting(settings.SECRET_KEY, request)
    )
    result = authomatic.login(DjangoAdapter(request, response), provider)

    if result:
        if result.error:
            messages.error(
                request,
                'There was an error signing you in. Please try again'
            )
            return HttpResponseRedirect(reverse('sign_in'))

        if result.user:
            # Then user is being redirected back from provider with their data
            #
            # OAuth 2.0 and OAuth 1.0a provide only limited user data on login,
            # We need to update the user to get more info.
            if not (result.user.name and result.user.id):
                result.user.update()

            provider = result.provider.name
            user = KagisoUser.get_user_from_auth_db(result.user.email)

            if user:
                _social_login(request, user.email, provider)
                return HttpResponseRedirect('/')
            else:
                gender = result.user.gender

                if gender:
                    # Form constants (region, gender) are in uppercase
                    gender = gender.upper()

                data = {
                    'provider': provider,
                    'email': result.user.email,
                    'first_name': result.user.first_name,
                    'last_name': result.user.last_name,
                    'gender': gender,
                    'birth_date': result.user.birth_date,
                }

                request.session['oauth_data'] = data
                return HttpResponseRedirect(reverse('sign_up'))

    # If result.user is None then user will be redirected to provider
    # to authenticate themselves, prior to being redirected back to this view.
    return response


def _social_login(request, email, provider):
    user = authenticate(
        email=email,
        strategy=provider,
    )
    login(request, user)


@never_cache
@login_required
def sign_out(request):
    request.user.record_sign_out()
    response = HttpResponseRedirect('/')
    logout(request)
    return response


@never_cache
@csrf_exempt
def forgot_password(request):
    reset_message = 'You will receive an email with reset instructions shortly'
    not_found_message = 'We could not find a user for that email address'

    if request.method == 'POST':
        form = forms.ForgotPasswordForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']
            user = KagisoUser.get_user_from_auth_db(email)

            if user:
                msg = EmailMessage()
                msg.to = [user.email]
                msg.from_email = get_setting(settings.AUTH_FROM_EMAIL, request)
                msg.subject = 'Password Reset'
                msg.template = get_setting(
                    settings.PASSWORD_RESET_EMAIL_TEMPLATE,
                    request
                )
                msg.substitution_data = {
                    'link': request.build_absolute_uri
                    (reverse('reset_password')),
                    'token': user.generate_reset_password_token(),
                    'user_id': user.id
                }
                msg.send()

                messages.success(request, reset_message)
                return HttpResponseRedirect(reverse('forgot_password'))
            else:
                messages.error(request, not_found_message)
                return HttpResponseRedirect(reverse('forgot_password'))
    else:
        form = forms.ForgotPasswordForm()

    return render(
        request,
        'kagiso_auth/forgot_password.html',
        {'form': form}
    )


@never_cache
@csrf_exempt
def reset_password(request):
    reset_message = 'Your password has been reset'

    if request.method == 'POST':
        form = forms.ResetPasswordForm(request.POST)

        if form.is_valid():
            # user_id is just for RESTFUL routing...
            # Token includes user_id and is validated server-side for tampering
            user_id = form.cleaned_data['user_id']
            token = form.cleaned_data['token']
            password = form.cleaned_data['password']

            user = KagisoUser.objects.filter(id=user_id).first()
            if user:
                user.reset_password(password, token)
                messages.success(request, reset_message)

            return HttpResponseRedirect(reverse('sign_in'))
    else:
        form = forms.ResetPasswordForm(
            initial={
                'user_id': request.GET.get('user_id'),
                'token': request.GET.get('token', ''),
            }
        )

    return render(
        request,
        'kagiso_auth/reset_password.html',
        {'form': form}
    )


@never_cache
@csrf_exempt
def resend_confirmation(request):
    not_found_message = 'We could not find a user for that email address'
    user = KagisoUser.objects.filter(email=request.GET['email']).first()

    if not user:
        messages.error(request, not_found_message)
        return HttpResponseRedirect('/')

    _send_confirmation_email(user, request)

    confirm_message = (
        'You will receive an email with confirmation instructions shortly. '
        'This link will expire within 24 hours.'
    )
    messages.success(request, confirm_message)

    return HttpResponseRedirect(reverse('sign_in'))
