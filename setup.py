try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='yahoofinancials',
    version='0.10',
    description='A powerful financial data module used for pulling both fundamental and technical data from Yahoo Finance',
    url='https://github.com/JECSand/yahoofinancials',
    download_url='https://github.com/JECSand/yahoofinancials/archive/0.10.tar.gz',
    author='Connor Sanders',
    author_email='connor@exceleri.com',
    license='MIT',
    keywords = ['finance data', 'stocks', 'commodities', 'cryptocurrencies', 'currencies', 'forex', 'yahoo finance'],
    packages=['yahoofinancials'],
    install_requires=[
        "requests",
        "beautifulsoup4",
        "pytz"
    ],
    classifiers=[],
    zip_safe=False
)
