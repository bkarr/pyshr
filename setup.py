from setuptools import setup, find_packages
import os

base_dir = os.path.dirname(__file__)

about = {}
with open(os.path.join(base_dir, "__about__.py")) as f:
    exec(f.read(), about)

CFFI_VERSION = '1.3.1'

setup(
    name=about['__title__'],
    version=about['__version__'],
    description=about['__summary__'],
    author=about['__author__'],
    author_email=about['__email__'],
    url=about['__uri__'],
    license=about['__license__'],
    py_modules=['pyshr', '__init__', '__about__'],
    zip_safe=False,
    install_requires=['cffi >= ' + CFFI_VERSION],
    setup_requires=['cffi >= ' + CFFI_VERSION],
    cffi_modules=["pyshr_build.py:ffi"],
)
