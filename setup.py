import codecs
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with codecs.open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='yahoofinancials',
    version='1.2',
    description='A powerful financial data module used for pulling both fundamental and technical data from Yahoo Finance',
    long_description=long_description,
    url='https://github.com/JECSand/yahoofinancials',
    download_url='https://github.com/JECSand/yahoofinancials/archive/1.2.tar.gz',
    author='Connor Sanders',
    author_email='connor@exceleri.com',
    license='MIT',
    keywords = ['finance data', 'stocks', 'commodities', 'cryptocurrencies', 'currencies', 'forex', 'yahoo finance'],
    packages=['yahoofinancials'],
    install_requires=[
        "beautifulsoup4",
        "pytz"
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'Topic :: Office/Business :: Financial :: Investment',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],
    zip_safe=False
)
