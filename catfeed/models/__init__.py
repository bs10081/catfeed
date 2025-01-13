from .admin import Admin
from .cat_profile import CatProfile
from .photo import Photo
from .feeding_record import FeedingRecord

# Alias Admin as User for Flask-Login
User = Admin

__all__ = ['Admin', 'CatProfile', 'Photo', 'FeedingRecord', 'User']
