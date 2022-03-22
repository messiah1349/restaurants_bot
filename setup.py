from setuptools import setup

setup(
    name='yerevan_restaurant',
    entry_points={
        'console_scripts': [
            'yerevan_restaurant = main:main',
        ],
    }
)
