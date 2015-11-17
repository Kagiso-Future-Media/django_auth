from authomatic import Authomatic
from authomatic.adapters import DjangoAdapter
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.db.utils import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template import RequestContext
from django.utils.safestring import mark_safe
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from . import forms
from .exceptions import EmailNotConfirmedError
from .models import KagisoUser


def _cas_credentials(request):
    site_name = RequestContext(request).get('site_name')

    if site_name == 'jacaranda':
        token = settings.JAC_CAS_TOKEN
        source_id = settings.JAC_CAS_SOURCE_ID
    elif site_name == 'ecr':
        token = settings.ECR_CAS_TOKEN
        source_id = settings.ECR_CAS_SOURCE_ID
    else:
        token = None
        source_id = None

    return {'cas_token': token, 'cas_source_id': source_id}


@never_cache
@csrf_exempt
def sign_up(request):
    confirm_message = \
        'You will receive an email with confirmation instructions shortly.' \
        'This link will expire within 24 hours.'
    error_message = 'You already have an account.'

    if request.user.is_authenticated():
        return HttpResponseRedirect('/')

    oauth_data = request.session.get('oauth_data')

    if request.method == 'POST':
        form = forms.SignUpForm.create(
            post_data=request.POST,
            oauth_data=oauth_data
        )

        if form.is_valid():
            try:
                if hasattr(request, 'site') and request.site:
                    form.site_id = request.site.id

                user = form.save(_cas_credentials(request))
            except IntegrityError:
                messages.error(request, error_message)
                return HttpResponseRedirect(reverse('sign_in'))

            # Social sign ins provide emails that have already been confirmed
            # via FB, Google etc...
            if not oauth_data:
                _send_confirmation_email(user, request)
                messages.success(request, confirm_message)
                # TODO: send to thank you page
                return HttpResponseRedirect('/')

            _social_login(request, user.email, oauth_data['provider'])
            return HttpResponseRedirect('/')
    else:
        form = forms.SignUpForm.create(oauth_data=oauth_data)

    return render(
        request,
        'kagiso_auth/sign_up.html',
        {'form': form},
    )


def _send_confirmation_email(user, request):
    site_name = RequestContext(request).get('site_name')

    msg = EmailMessage()

    if site_name == 'jacaranda':
        msg.template_name = settings.JAC_SIGN_UP_TEMPLATE
        msg.from_email = 'noreply@jacarandafm.com'
    elif site_name == 'ecr':
        msg.template_name = settings.ECR_SIGN_UP_TEMPLATE
        msg.from_email = 'noreply@ecr.co.za'

    msg.subject = 'Confirm Your Account'
    msg.to = [user.email]
    msg.global_merge_vars = {
        'link': request.build_absolute_uri(reverse('confirm_account')),
        'token': user.confirmation_token,
        'user_id': user.id,
        'first_name': user.first_name
    }
    msg.use_template_subject = True
    msg.use_template_from = True
    msg.send()


@never_cache
def confirm_account(request):
    confirm_message = 'We have confirmed your details, please sign in below'

    user_id = request.GET.get('user_id')
    token = request.GET.get('token')

    user = get_object_or_404(KagisoUser, id=user_id)
    user.override_cas_credentials(_cas_credentials(request))
    user.confirm_email(token)

    messages.success(request, confirm_message)
    return HttpResponseRedirect(reverse('sign_in'))


@never_cache
@csrf_exempt
def sign_in(request):
    # TODO: Redirect to where they came from

    # TODO: Move to decorator
    if request.user.is_authenticated():
        return HttpResponseRedirect('/')

    if request.method == 'POST':
        form = forms.SignInForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                user = authenticate(
                    email=email,
                    password=password,
                    cas_credentials=_cas_credentials(request)
                )

                if user:
                    response = HttpResponseRedirect('/')
                    user.override_cas_credentials(_cas_credentials(request))
                    response.set_cookie('signed_in',
                                        value='true',
                                        max_age=2544)
                    login(request, user)
                    return response
                else:
                    messages.error(request, 'Incorrect email or password')
            except EmailNotConfirmedError:
                resend_str = 'Please first confirm your email address. ' \
                    '<a href="/resend_confirmation?email={email}">' \
                    'Resend confirmation email</a>'.format(email=email)
                messages.error(
                    request,
                    mark_safe(resend_str)
                )
    else:
        form = forms.SignInForm()

    return render(
        request,
        'kagiso_auth/sign_in.html',
        {'form': form}
    )


@never_cache
def oauth(request, provider):
    response = HttpResponse()
    site_name = RequestContext(request)['site_name']
    authomatic = Authomatic(
        settings.AUTHOMATIC_CONFIG[site_name],
        settings.SECRET_KEY
    )
    result = authomatic.login(DjangoAdapter(request, response), provider)

    if result:
        if result.error:
            print(result.error)
            # TODO: Send back where they came from

        if result.user:
            # Then user is being redirected back from provider with their data
            #
            # OAuth 2.0 and OAuth 1.0a provide only limited user data on login,
            # We need to update the user to get more info.
            if not (result.user.name and result.user.id):
                result.user.update()

            email = result.user.data.get('email')
            provider = result.provider.name
            user = KagisoUser.objects.filter(email=email).first()

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
        cas_credentials=_cas_credentials(request)
    )
    login(request, user)


@never_cache
@login_required
def sign_out(request):
    try:
        request.user.override_cas_credentials(_cas_credentials(request))
        request.user.record_sign_out()
    finally:
        # HACK: CMS admin users are on a different CAS account to regular
        # JAC or ECR users, yet we don't actually care when admins sign out
        # So just sign out regardless
        response = HttpResponseRedirect('/')
        response.delete_cookie('signed_in')
        logout(request)
        return response


@never_cache
@csrf_exempt
def forgot_password(request):
    site_name = RequestContext(request).get('site_name')

    reset_message = 'You will receive an email with reset instructions shortly'
    not_found_message = 'We could not find a user for that email address'

    if request.method == 'POST':
        form = forms.ForgotPasswordForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']
            user = KagisoUser.objects.filter(email=email).first()

            if user:
                user.override_cas_credentials(_cas_credentials(request))

                msg = EmailMessage()

                if site_name == 'jacaranda':
                    msg.template_name = settings.JAC_PASSWORD_RESET_TEMPLATE
                    msg.from_email = 'noreply@jacarandafm.com'
                elif site_name == 'ecr':
                    msg.template_name = settings.ECR_PASSWORD_RESET_TEMPLATE
                    msg.from_email = 'noreply@ecr.co.za'

                msg.subject = 'Password Reset'
                msg.to = [user.email]
                msg.global_merge_vars = {
                    'link': request.build_absolute_uri
                    (reverse('reset_password')),
                    'token': user.generate_reset_password_token(),
                    'user_id': user.id
                }
                msg.use_template_subject = True
                msg.use_template_from = True
                msg.send()
                messages.success(request, reset_message)
                return HttpResponseRedirect('/')
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
                user.override_cas_credentials(_cas_credentials(request))
                user.reset_password(password, token)
                messages.success(request, reset_message)

                return HttpResponseRedirect('/')
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

    confirm_message = \
        'You will receive an email with confirmation instructions shortly.' \
        'This link will expire within 24 hours.'

    messages.success(request, confirm_message)

    return HttpResponseRedirect(reverse('sign_in'))
