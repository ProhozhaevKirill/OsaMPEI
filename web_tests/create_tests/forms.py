from django import forms
from .models import AboutExpressions, AboutTest


class TestForm(forms.ModelForm):
    class Meta:
        model = AboutTest
        fields = ['name_tests',
                  'time_to_solution',
                  'is_published',
                  'name_slug_tests',
                  'expressions']
        
        
class ExpressionForm(forms.ModelForm):
    class Meta:
        model = AboutExpressions
        fields = ['user_expression',
                  'user_ans',
                  'points_for_solve',
                  'user_eps',
                  'user_type']
        