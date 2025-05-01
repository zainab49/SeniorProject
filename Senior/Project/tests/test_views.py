import pytest
from django.urls import reverse
from rest_framework import status

@pytest.mark.django_db
def test_view_response(client):
    url = reverse('your_view_name')  # Replace with your actual view name
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_view_template_used(client):
    url = reverse('your_view_name')  # Replace with your actual view name
    response = client.get(url)
    assert 'your_template_name.html' in [t.name for t in response.templates]  # Replace with your actual template name