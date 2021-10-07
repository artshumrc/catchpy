from .base import *
from django.core.exceptions import ImproperlyConfigured

try:
    cidr_list = os.environ.get('ALLOWED_CIDR_NETS')
    ALLOWED_CIDR_NETS = cidr_list.split()
    print("ALLOWED CIDR NETS: -------------")
    print(ALLOWED_CIDR_NETS)
except ImproperlyConfigured:
    print("Allowed CIDR Nets is not set")

try:
    MIDDLEWARE += [
        'allow_cidr.middleware.AllowCIDRMiddleware',
        'corsheaders.middleware.CorsMiddleware'
    ]
except:
    print("Cannot add CIDR Nets Middleware")