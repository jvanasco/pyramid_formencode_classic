"""pyramid_formencode_classic installation script.
"""

import os
import re

from setuptools import find_packages
from setuptools import setup

HERE = os.path.dirname(__file__)

long_description = description = (
    "An implementation of the classic Pylons formencode validation, for Pyramid."
)
with open(os.path.join(HERE, "README.md")) as r_file:
    long_description = r_file.read()

# store version in the init.py
with open(
    os.path.join(HERE, "src", "pyramid_formencode_classic", "__init__.py")
) as v_file:
    VERSION = (
        re.compile(r'''.*__VERSION__ = "(.*?)"''', re.S).match(v_file.read()).group(1)
    )
    assert VERSION


requires = [
    "pyramid",
    "formencode>=2.0.0",
    "typing_extensions",  # TypedDict
]
testing_extras = [
    "pytest",
    "mypy",
    "pyramid_mako",
    "webob",
]

setup(
    name="pyramid_formencode_classic",
    author="Jonathan Vanasco",
    author_email="jonathan@findmeon.com",
    version=VERSION,
    url="https://github.com/jvanasco/pyramid_formencode_classic",
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="BSD",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "": [
            "py.typed",
            "debugtoolbar/panels/templates/*",
        ],
    },
    zip_safe=False,
    install_requires=requires,
    extras_require={
        "testing": testing_extras,
    },
    classifiers=[
        "Intended Audience :: Developers",
        "Framework :: Pyramid",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
