from setuptools import setup
from Cython.Build import cythonize

setup(
    name="matching_engine",
    ext_modules=cythonize("order_matching.pyx", language_level="3"),
    zip_safe=False,
)
