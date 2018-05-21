from setuptools import setup

setup(
    name='link-checker',
    version='0.1.0',
    py_modules=['checker'],
    install_requires=[
        'Click',
        'requests',
        'bs4',
    ],
    entry_points='''
        [console_scripts]
        link-checker=checker:check
    ''',
)
