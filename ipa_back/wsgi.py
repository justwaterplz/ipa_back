"""
WSGI config for ipa_back project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ipa_back.settings')

application = get_wsgi_application() 