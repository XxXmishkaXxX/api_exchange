from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize([
        "engine/matching_engine.pyx",
        "engine/order.pyx",
        "engine/order_book.pyx"
    ]),
    zip_safe=False,
)
