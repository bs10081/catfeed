from .admin import Admin
from .cat_profile import CatProfile
from .photo import Photo
from .feeding_record import FeedingRecord
from .settings import Settings
from .biography import Biography

# Alias Admin as User for Flask-Login
User = Admin

__all__ = ['Admin', 'CatProfile', 'Photo', 'FeedingRecord', 'User', 'Settings', 'Biography']
