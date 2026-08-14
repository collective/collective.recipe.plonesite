"""
This module contains the tool of collective.recipe.plonesite
"""
from pathlib import Path

from setuptools import setup


version = '2.0.0.dev0'

long_description = '\n\n'.join(
    Path(filename).read_text(encoding='utf-8')
    for filename in ('README.rst', 'CONTRIBUTORS.rst', 'CHANGES.rst')
)

entry_point = 'collective.recipe.plonesite:Recipe'
entry_points = {
    'zc.buildout': [
        f'default = {entry_point}',
    ]
}

setup(
    name='collective.recipe.plonesite',
    version=version,
    description='A buildout recipe to create and update a plone site',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    classifiers=[
        'Framework :: Buildout',
        'Framework :: Plone',
        'Framework :: Plone :: 6.1',
        'Framework :: Plone :: 6.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='plone buildout recipe',
    author='Clayton Parker',
    author_email='info@sixfeetup.com',
    url='https://github.com/collective/collective.recipe.plonesite',
    license='ZPL',
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3.10',
    install_requires=[
        'setuptools',
        'zc.buildout',
    ],
    extras_require=dict(
        test=[
            'zc.buildout[test]',
            'zope.testrunner',
        ],
        upgrade=['collective.upgrade>=1.0rc1'],
    ),
    entry_points=entry_points,
)
