from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize(
        ["engine/order.pyx", "engine/order_book.pyx", "engine/matching_engine.pyx"],
        language_level=3
    ),
)