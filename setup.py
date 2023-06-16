"""pyramid_formencode_classic installation script.
"""
import os
import re

from setuptools import setup
from setuptools import find_packages

HERE = os.path.dirname(__file__)

long_description = description = (
    "An implementation of the classic Pylons formencode validation, for Pyramid",
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


requires = [
    "pyramid",
    "formencode>=2.0.0",
]
tests_require = [
    "mypy",
    "pyramid_mako",
    "webob",
]
testing_extras = tests_require + [
    "pytest",
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
    packages=find_packages(
        where="src",
    ),
    package_dir={"": "src"},
    package_data={"pyramid_formencode_classic": ["py.typed"]},
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    tests_require=tests_require,
    extras_require={
        "testing": testing_extras,
    },
    test_suite="tests",
    classifiers=[
        "Intended Audience :: Developers",
        "Framework :: Pyramid",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: BSD License",
    ],
)
