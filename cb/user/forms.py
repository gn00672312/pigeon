# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

User = get_user_model()


class EditUserForm(forms.ModelForm):
    """
    Class for editing members.
    """
    pk = forms.IntegerField()
    username = forms.RegexField(max_length=100, regex=r'^[\w.@+-]+$',
                                error_messages={'required': _('Login ID is a required field.'),
                                                'invalid': _('Login ID may contain only letters,'
                                                             ' numbers and @/./+/-/_ characters.')})
    password1 = forms.CharField(max_length=128, required=False)
    password2 = forms.CharField(max_length=128, required=False)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'is_superuser')

    def clean_password2(self):
        password1 = self.cleaned_data['password1']
        password2 = self.cleaned_data['password2']
        if password1 != password2:
            raise forms.ValidationError(_("The two password fields didn't match."))
        return password2

    def save(self, commit=True, admin_editing=False):
        u = User.objects.get(pk=self.cleaned_data['pk'])
        u.username = self.cleaned_data['username']
        u.first_name = self.cleaned_data['first_name']
        u.last_name = self.cleaned_data['last_name']
        u.email = self.cleaned_data['email']

        if admin_editing:
            u.is_superuser = self.cleaned_data['is_superuser']

        if self.cleaned_data['password2']:
            u.set_password(self.cleaned_data['password2'])

        if commit:
            u.save()

        return u
