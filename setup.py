#!/usr/bin/env python3
"""
Setup script for Fun with Maps.
"""

import os

from setuptools import find_packages, setup

# Read the contents of your README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# Read requirements from requirements.txt
with open(os.path.join(this_directory, "requirements.txt"), encoding="utf-8") as f:
    requirements = [
        line.strip() for line in f if line.strip() and not line.startswith("#")
    ]

setup(
    name="fun-with-maps",
    version="1.0.0",
    author="Fun with Maps Team",
    author_email="",
    description="A comprehensive geospatial analysis toolkit for working with world maps",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/fun-with-maps",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pre-commit>=3.6.0",
            "black>=23.12.0",
            "isort>=5.13.0",
            "flake8>=7.0.0",
            "flake8-unused-arguments>=0.0.13",
            "flake8-import-order>=0.18.2",
        ]
    },
    entry_points={
        "console_scripts": [
            "fun-with-maps=scripts.main:main",
            "fun-with-maps-cli=fun_with_maps.cli:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
