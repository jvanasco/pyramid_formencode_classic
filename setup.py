"""pyramid_formencode_classic installation script.
"""
import os

from setuptools import setup
from setuptools import find_packages



def get_docs():
    result = []
    in_docs = False
    f = open(os.path.join(os.path.dirname(__file__), 'pyramid_formencode_classic.py'))
    try:
        for line in f:
            if in_docs:
                if line.lstrip().startswith(':copyright:'):
                    break
                result.append(line[4:].rstrip())
            elif line.strip() == 'r"""':
                in_docs = True
    finally:
        f.close()
    return '\n'.join(result)



requires = [
    "pyramid", 
    "FormEncode>=1.2.4",
    ]

setup(name="pyramid_formencode_classic",
      version="0.0.5",
      description="an implementation of the classic pylons formencode validation, for pyramid",
      long_description=get_docs(),
      classifiers=[
        "Intended Audience :: Developers",
        "Framework :: Pylons",
        "Programming Language :: Python",
        "License :: OSI Approved :: BSD License",
        ],
      keywords="web pyramid",
      py_modules=['pyramid_formencode_classic'],
      author="Jonathan Vanasco",
      author_email="jonathan@findmeon.com",
      url="https://github.com/jvanasco/pyramid_formencode_classic",
      license="MIT",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      tests_require = requires,
      install_requires = requires,
      )

