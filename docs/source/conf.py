# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from os import path
import sys

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Cerulean'
copyright = '2018-2019, 2024, The Netherlands eScience Center and VU University Amsterdam'
author = 'Lourens Veen'

release = '0.3.8.dev0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# apidoc needs to be able to import cerulean
here = path.dirname(__file__)
sys.path.insert(0, path.abspath(path.join(here, '..', '..')))

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon']

autodoc_default_options = {
        'special-members': '__init__'
        }


templates_path = ['_templates']
exclude_patterns = []

root_doc = 'index'


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

