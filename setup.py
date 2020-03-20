import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pybt",
    version="0.0.1",
    author="Evgenii Safronov",
    author_email="safoex@gmail.com",
    description="Behavior Tree in Python. Again. Planning Included",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/safoex/pybt",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)