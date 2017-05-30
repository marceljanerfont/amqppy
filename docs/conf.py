# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '../')
# needs_sphinx = '1.0'

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode',
              'sphinx.ext.intersphinx']

intersphinx_mapping = {'python': ('https://docs.python.org/3/',
                                  'https://docs.python.org/3/objects.inv'),
                       'pika': ('https://pika.readthedocs.io',
                                'http://pika.readthedocs.io/en/latest/objects.inv')}

templates_path = ['_templates']

source_suffix = '.rst'
master_doc = 'index'

project = 'amqppy'
copyright = '2017, Marcel Janer Font and others.'

import amqppy
import amqppy.publisher
import amqppy.consumer
release = amqppy.__version__
version = '.'.join(release.split('.')[0:2])
print("***** amqppy release: {}, version: {} *****".format(release, version))

exclude_patterns = ['_build']
add_function_parentheses = True
add_module_names = True
show_authors = True
pygments_style = 'sphinx'
modindex_common_prefix = ['amqppy']
html_theme = 'default'
# html_static_path = ['_static']
htmlhelp_basename = 'amqppydoc'

import sphinx_rtd_theme
html_theme = "sphinx_rtd_theme"
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
