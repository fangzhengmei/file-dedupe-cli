from setuptools import setup, find_packages

setup(
    name="file-dedupe",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.0.0",
    ],
    entry_points={
        "console_scripts": [
            "file-dedupe=file_dedupe.cli:main",
        ],
    },
    python_requires=">=3.8",
)
