from setuptools import setup

setup(
    name='betacode',
    version='0.1',
    description='Decode Greek and Hebrew betacode',
#    long_description=open('README.rst').read(),
    url='https://github.com/ninjaaron/betacode',
    author='Aaron Christianson',
    author_email='ninjaaron@gmail.com',
    keywords='betacode hebrew greek catss tlg',
    packages = ['betacode'],
    entry_points={'console_scripts': 'betacode=betacode.script:main'},)
