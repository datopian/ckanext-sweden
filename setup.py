from setuptools import setup, find_packages
import sys, os

version = '1.0'

setup(
    name='ckanext-sweden',
    version=version,
    description="Custom CKAN extension for the Swedish data portal",
    long_description='''
    ''',
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Tryggvi Bj\xc3\xb6rgvinsson',
    author_email='tryggvi.bjorgvinsson@okfn.org',
    url='',
    license='AGPL',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.sweden'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points='''
        [ckan.plugins]
        # Add plugins here, e.g.
        sweden_blog=ckanext.sweden.blog.plugin:BlogPlugin
        sweden_theme=ckanext.sweden.theme.plugin:ThemePlugin
        dcat_rdf_harvester=ckanext.sweden.dcat.harvester:RDFDCATHarvester

        [ckan.rdf.profiles]
        euro_dcat_ap=ckanext.sweden.dcat.profiles:EuropeanDCATAPProfile
        sweden_dcat_ap=ckanext.sweden.dcat.profiles:SwedishDCATAPProfile

        [paste.paster_command]
        sweden_blog_init = ckanext.sweden.blog.commands.blog_init:InitDB
    ''',
)
