import os
import sys
import django

sys.path.insert(0, os.path.abspath('..'))

os.environ['DJANGO_SETTINGS_MODULE'] = 'OnBoAArrrd.settings'
django.setup()

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
]

html_theme = 'sphinx_rtd_theme'
