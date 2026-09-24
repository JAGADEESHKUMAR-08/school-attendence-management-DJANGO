from django import forms

from .models import ClassRoom, User


class LoginForm(forms.Form):
    role = forms.ChoiceField(
        choices=User.Role.choices,
        initial=User.Role.STUDENT,
        widget=forms.RadioSelect,
        label='I am a',
    )
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))


class RegisterForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=User.Role.choices,
        initial=User.Role.STUDENT,
        widget=forms.RadioSelect,
        label='I am a',
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
    )
    password2 = forms.CharField(
        label='Confirm password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Repeat password'}),
    )

    class Meta:
        model = User
        fields = ['username', 'full_name', 'email']

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get('password1')
        password2 = cleaned.get('password2')
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'The two passwords do not match.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class StudentForm(forms.ModelForm):
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
        required=True,
    )

    class Meta:
        model = User
        fields = ['username', 'full_name', 'email']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.STUDENT
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class ClassRoomForm(forms.ModelForm):
    students = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role=User.Role.STUDENT),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = ClassRoom
        fields = ['name', 'teacher']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher'].queryset = User.objects.filter(role=User.Role.TEACHER)
        self.fields['teacher'].required = False
        self.fields['teacher'].empty_label = '---- Assign a teacher ----'
