from setuptools import setup
from Cython.Build import cythonize

setup(
    name='sensai',
    ext_modules=cythonize([
        "sensai.py",
        "prompts.py"
    ], compiler_directives={'language_level': "3"}),
    zip_safe=False,
)
