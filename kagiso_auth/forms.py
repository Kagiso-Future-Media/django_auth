from datetime import datetime

from django import forms
from django.forms.extras import widgets
from django.utils import timezone


from .models import KagisoUser


def validate_passwords_match(form):
    password = form.cleaned_data.get('password')
    confirm_password = form.cleaned_data.get('confirm_password')

    if password and password != confirm_password:
        message = 'Passwords do not match'
        form.add_error('confirm_password', message)


class SignInForm(forms.Form):
    email = forms.EmailField(label='Email Address')
    password = forms.CharField(widget=forms.PasswordInput())
    remember_me = forms.BooleanField(required=False, initial=True)


class SignUpForm(forms.Form):
    GENDER_CHOICES = (('MALE', 'Male'), ('FEMALE', 'Female'),)
    REGION_CHOICES = (
        ('', 'Select Region'),
        ('EASTERN_CAPE', 'Eastern Cape'),
        ('FREE_STATE', 'Free State'),
        ('GAUTENG', 'Gauteng'),
        ('KWAZULU_NATAL', 'Kwazulu Natal'),
        ('LIMPOPO', 'Limpopo'),
        ('MPUMALANGA', 'Mpumalanga'),
        ('NORTH_WEST', 'North West'),
        ('NORTHERN_CAPE', 'Northern Cape'),
        ('WESTERN_CAPE', 'Western Cape'),
    )
    ALERT_CHOICES = (('EMAIL', 'Email'), ('SMS', 'SMS'))
    MOBILE_REGEX = r'^\d{10}$'
    EMAIL_REGEX = '[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,4}$'

    # --- Form fields ---
    email = forms.EmailField(
        widget=forms.TextInput(attrs={
            'placeholder': 'eg. name@emailaddress.com',
            'pattern': EMAIL_REGEX,
            'title': 'eg. name@emailaddress.com',
            'required': 'true'}),
        error_messages={'required': 'Please enter a valid email address'}
    )
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'eg. John',
            'required': 'true'}),
        error_messages={'required': 'Please enter your name'}
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'placeholder': 'eg. Doe',
            'required': 'true'}),
        error_messages={'required': 'Please enter your last name'}
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'required': 'true'}),
        min_length=8
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'required': 'true'})
    )
    mobile = forms.RegexField(
        regex=MOBILE_REGEX,
        widget=forms.TextInput(attrs={
            'placeholder': 'eg. 0821234567',
            'pattern': MOBILE_REGEX,
            'title': 'eg. 0821234567',
            'required': 'true'}),
        error_messages={
            'required': 'Correct mobile number format: 0821234567'
        },
        error_message=('Correct mobile number format: 0821234567')
    )
    gender = forms.ChoiceField(
        error_messages={'required': 'Please select a gender'},
        choices=GENDER_CHOICES,
        widget=forms.RadioSelect
    )
    region = forms.ChoiceField(
        error_messages={'required': 'Please select a region'},
        choices=REGION_CHOICES
    )
    birth_date = forms.DateField(
        label='Birthday',
        widget=widgets.SelectDateWidget(
            months={
                0: 'Select Month',
                1: 'January',
                2: 'February',
                3: 'March',
                4: 'April',
                5: 'May',
                6: 'June',
                7: 'July',
                8: 'August',
                9: 'September',
                10: 'October',
                11: 'November',
                12: 'December',
            },
            years=['Select Year'] +
            list(range(datetime.now().year, 1900, -1))
        )
    )
    alerts = forms.MultipleChoiceField(
        label='How would you like to receive alerts?',
        choices=ALERT_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    # --- Instance variables ---
    social_sign_in = False

    @classmethod
    def create(cls, post_data=None, oauth_data=None):
        form = cls(post_data, initial=oauth_data)

        # Social sign ups don't require passwords...
        if oauth_data:
            form.social_sign_in = True
            form._remove_password_fields()

        return form

    def clean(self):
        validate_passwords_match(self)
        return self.cleaned_data

    def save(self, app_name):
        user = KagisoUser()
        user.email = self.cleaned_data['email']

        if self.social_sign_in:
            user.email_confirmed = timezone.now()
        else:
            user.set_password(self.cleaned_data['password'])

        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.profile = {
            'mobile': self.cleaned_data['mobile'],
            'gender': self.cleaned_data['gender'],
            'region': self.cleaned_data['region'],
            'birth_date': str(self.cleaned_data['birth_date']),
            'alerts': self.cleaned_data['alerts'],
        }
        user.created_via = app_name

        user.save()
        return user

    def _remove_password_fields(self):
        del self.fields['password']
        del self.fields['confirm_password']


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        label='Enter your email address'
    )


class ResetPasswordForm(forms.Form):
    user_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    token = forms.CharField(required=False, widget=forms.HiddenInput())
    password = forms.CharField(widget=forms.PasswordInput(), min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput())

    def clean(self):
        validate_passwords_match(self)
        return self.cleaned_data
