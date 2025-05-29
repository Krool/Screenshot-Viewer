from setuptools import setup, find_packages

setup(
    name="steam-screenshots-viewer",
    version="1.0.0",
    description="A modern viewer for Steam screenshots with a Steam-like interface",
    author="Kenny Preston",
    packages=find_packages(),
    install_requires=[
        "PyQt6>=6.0.0"
    ],
    entry_points={
        "console_scripts": [
            "steam-screenshots-viewer=steam_viewer.main:main"
        ]
    },
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: Qt",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Desktop Environment",
        "Topic :: Games/Entertainment",
        "Topic :: Multimedia :: Graphics :: Viewers",
    ],
) 