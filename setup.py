import codecs
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with codecs.open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='yahoofinancials',
    version='1.19',
    description='A powerful financial data module used for pulling both fundamental and technical data from Yahoo Finance',
    long_description=long_description,
    url='https://github.com/JECSand/yahoofinancials',
    download_url='https://github.com/JECSand/yahoofinancials/archive/1.19.tar.gz',
    author='Connor Sanders',
    author_email='connor@exceleri.com',
    license='MIT',
    keywords=['finance data', 'stocks', 'commodities', 'cryptocurrencies', 'currencies', 'forex', 'yahoo finance'],
    packages=['yahoofinancials'],
    install_requires=[
        "pytz>=2022.5",
        "requests>=2.31",
        "appdirs>=1.4.4",
        "frozendict>=2.3.4",
        "peewee>=3.16.2",
        "beautifulsoup4>=4.11.1",
        "lxml>=4.9.1",
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'Topic :: Office/Business :: Financial :: Investment',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    zip_safe=False
)
