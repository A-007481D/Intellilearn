with open("config/settings.py", "r") as f:
    content = f.read()

# Add corsheaders to INSTALLED_APPS
if '"corsheaders"' not in content and "'corsheaders'" not in content:
    content = content.replace(
        '"apps.authentication",', '"corsheaders",\n    "apps.authentication",'
    )

# Add cors middleware before SecurityMiddleware
if "CorsMiddleware" not in content:
    content = content.replace(
        "MIDDLEWARE = [\n",
        'MIDDLEWARE = [\n    "corsheaders.middleware.CorsMiddleware",\n',
    )

# Add new settings at the bottom
new_settings = """
# CORS
CORS_ALLOW_ALL_ORIGINS = True  # dev only

# Email (console backend for dev)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@intellilearn.com'

# REST Framework — add pagination
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}
"""

if "CORS_ALLOW_ALL_ORIGINS" not in content:
    content += "\n" + new_settings

with open("config/settings.py", "w") as f:
    f.write(content)
