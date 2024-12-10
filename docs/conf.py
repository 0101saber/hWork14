import sys
import os

sys.path.append(os.path.abspath('..'))

project = 'Home Work 14'
copyright = '2024, Anna'
author = 'Anna'
release = '1'
extensions = ['sphinx.ext.autodoc']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'nature'
html_static_path = ['_static']
