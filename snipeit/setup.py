from setuptools import setup

setup(
    name='snipeit_cli',
    version='0.1',
    packages=[''],
    py_modules=['snipeit_cli', 'snipeit_api'],
    entry_points={
        'console_scripts': [
            'snipeit = snipeit_cli:main'
        ]
    },
)
