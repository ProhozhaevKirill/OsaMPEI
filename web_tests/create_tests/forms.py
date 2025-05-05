from django import forms
from .models import AboutExpressions, AboutTest
from datetime import timedelta


class TestForm(forms.ModelForm):
    class Meta:
        model = AboutTest
        fields = ['name_tests',
                  'time_to_solution',
                  'is_published',
                  'name_slug_tests',
                  'expressions',
                  'description',
                  'subj']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:  # только при создании, не при редактировании
            self.initial['time_to_solution'] = timedelta(hours=1, minutes=30)
        
        
class ExpressionForm(forms.ModelForm):
    class Meta:
        model = AboutExpressions
        fields = ['user_expression',
                  'user_ans',
                  'points_for_solve',
                  'user_eps',
                  'user_type']
        