from setuptools import setup, find_packages

setup(
    name="vantage-agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "httpx>=0.24.0",
        "urllib3>=1.26.0",
    ],
)
