import pytest
from django.urls import reverse
from .models import YourModel

@pytest.mark.django_db
def test_database_functionality():
    instance = YourModel.objects.create(field='value')
    assert instance.field == 'value'