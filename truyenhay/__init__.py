from __future__ import absolute_import, unicode_literals

# Celery application as a module-level variable
from .celery import app as celery_app

__all__ = ['celery_app']
