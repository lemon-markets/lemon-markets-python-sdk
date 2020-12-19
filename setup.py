import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="lemon_markets",
    version="0.0.1",
    author="Marcel Katenhusen",
    author_email="marcel@lemon.markets",
    description="Official SDK for the lemon.markets trading & market data API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lemon-markets/lemon-markets-python-sdk",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
