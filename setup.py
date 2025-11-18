from setuptools import setup, find_packages
import os

# Read README
def read_file(filename):
    with open(os.path.join(os.path.dirname(__file__), filename), encoding='utf-8') as f:
        return f.read()

setup(
    name="dnacryptdb",
    version="1.0.0",
    author="Harshith Madhavaram",
    author_email="madhavaram.harshith2412@gmail.com",
    description="A polyglot database system with custom query language for MySQL and MongoDB",
    long_description=read_file('README.md'),
    long_description_content_type="text/markdown",
    url="https://github.com/Harshith2412/dnacryptdb",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "mysql-connector-python>=8.0.0",
        "pymongo>=4.0.0",
    ],
    entry_points={
        "console_scripts": [
            "dnacryptdb=dnacryptdb.cli:main",
        ],
    },
    keywords="database polyglot mysql mongodb dnacrypt query-language",
    project_urls={
        "Bug Reports": "https://github.com/Harshith2412/dnacryptdb/issues",
        "Source": "https://github.com/Harshith2412/dnacryptdb",
    },
)