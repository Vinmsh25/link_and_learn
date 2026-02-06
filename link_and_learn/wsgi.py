"""
WSGI config for Link & Learn project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'link_and_learn.settings')
application = get_wsgi_application()
