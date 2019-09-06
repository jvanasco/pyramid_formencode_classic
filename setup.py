"""pyramid_formencode_classic installation script.
"""
import os
import re

from setuptools import setup
from setuptools import find_packages


# store version in the init.py
with open(
    os.path.join(os.path.dirname(__file__), "pyramid_formencode_classic", "__init__.py")
) as v_file:
    VERSION = (
        re.compile(r'''.*__VERSION__ = "(.*?)"''', re.S).match(v_file.read()).group(1)
    )


requires = ["pyramid", "formencode>=2.0.0a", "six"]

setup(
    name="pyramid_formencode_classic",
    author="Jonathan Vanasco",
    author_email="jonathan@findmeon.com",
    version=VERSION,
    url="https://github.com/jvanasco/pyramid_formencode_classic",
    description="an implementation of the classic pylons formencode validation, for pyramid",
    long_description="an implementation of the classic pylons formencode validation, for pyramid",
    license="BSD",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    test_suite="pyramid_formencode_classic.tests",
    classifiers=[
        "Intended Audience :: Developers",
        "Framework :: Pyramid",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
    ],
)
