# docs/conf.py
import os
import sys
sys.path.insert(0, os.path.abspath('..'))

# Project information
project = 'djangoMVP'
author = 'heane'
release = '0.1.0'
version = '0.1.0'

# Sphinx extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
]

# Intersphinx mappings for Python and Django docs
intersphinx_mapping = {
    'python': ('https://docs.python.org/3.12', None),
    'django': ('https://docs.djangoproject.com/en/5.2', None),
}

# Templates and static
templates_path = ['_templates']
exclude_patterns = []

# HTML output options
theme = 'sphinx_rtd_theme'
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static'] 