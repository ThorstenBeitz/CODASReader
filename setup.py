try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='CODASReader',
    version='1.0',
    author='Thorsten Beitz',
    author_email='thorsten.beitz@ucdconnect.ie',
    maintainer='John Quinn',
    maintainer_email='john.quinn@ucd.ie',
    packages=['CODASReader'],
    license='LICENSE.txt',
    description='Python class to read CODAS files and translate to ASCII',
    long_description=open('README.txt').read(),
)