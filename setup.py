from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="dnacryptdb",
    version="2.0.0",
    author="Harshith Madhavaram",
    author_email="harshith@northeastern.edu",
    description="A secure triglot database system for DNA-based cryptographic applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/YOUR_USERNAME/dnacryptdb",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Database",
        "Topic :: Security :: Cryptography",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "mysql-connector-python>=8.0.0",
        "pymongo>=4.0.0",
        "neo4j>=5.0.0",
        "cryptography>=41.0.0",
    ],
    entry_points={
        "console_scripts": [
            "dnacryptdb=dnacryptdb.cli:main",
        ],
    },
    keywords="database polyglot mysql mongodb neo4j dnacrypt cryptography encryption bioinformatics",
    project_urls={
        "Bug Reports": "https://github.com/YOUR_USERNAME/dnacryptdb/issues",
        "Source": "https://github.com/YOUR_USERNAME/dnacryptdb",
        "Documentation": "https://github.com/YOUR_USERNAME/dnacryptdb/blob/main/README.md",
    },
)