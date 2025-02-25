from django import forms
from .models import StudentResult


class StudentResultForm(forms.ModelForm):
    class Meta:
        model = StudentResult
        fields = '__all__'
