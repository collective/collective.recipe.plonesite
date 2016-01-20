# -*- coding: utf-8 -*-
"""
This module contains the tool of collective.recipe.plonesite
"""
import os
from setuptools import setup, find_packages


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

version = '1.9.5'

long_description = (
    read('README.rst')
    + '\n' +
    'Detailed Documentation\n'
    '**********************\n'
    + '\n' +
    read('collective', 'recipe', 'plonesite', 'README.rst')
    + '\n' +
    'Contributors\n'
    '************\n'
    + '\n' +
    read('CONTRIBUTORS.rst')
    + '\n' +
    'Change history\n'
    '**************\n'
    + '\n' +
    read('CHANGES.rst')
    + '\n' +
    'Download\n'
    '********\n')

entry_point = 'collective.recipe.plonesite:Recipe'
entry_points = {"zc.buildout": ["default = %s" % entry_point]}

tests_require = ['zope.testing', 'zc.buildout']

setup(
    name='collective.recipe.plonesite',
    version=version,
    description="A buildout recipe to create and update a plone site",
    long_description=long_description,
    # Get more strings from:
    # http://www.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Framework :: Buildout',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: Zope Public License',
    ],
    keywords='plone buildout recipe',
    author='Clayton Parker',
    author_email='info@sixfeetup.com',
    url='http://sixfeetup.com',
    license='ZPL',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['collective', 'collective.recipe'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'zc.buildout'
        # -*- Extra requirements: -*-
    ],
    tests_require=tests_require,
    extras_require=dict(
        tests=tests_require,
        upgrade=['collective.upgrade>=1.0rc1']),
    test_suite='collective.recipe.plonesite.tests.test_docs.test_suite',
    entry_points=entry_points,
)
