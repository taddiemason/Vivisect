#!/usr/bin/env python3
"""Setup script for Vivisect Digital Forensics Suite"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    with open('README.md', 'r', encoding='utf-8') as f:
        return f.read()

setup(
    name='vivisect-forensics',
    version='1.0.0',
    description='Comprehensive Digital Forensics Suite for Debian',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    author='Vivisect Team',
    url='https://github.com/vivisect/vivisect',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    python_requires='>=3.8',
    install_requires=[
        'python-magic>=0.4.27',
        'scapy>=2.5.0',
        'colorama>=0.4.6',
        'tabulate>=0.9.0',
    ],
    extras_require={
        'full': [
            'yara-python>=4.3.0',
            'pefile>=2023.2.7',
            'pyelftools>=0.29',
        ],
    },
    entry_points={
        'console_scripts': [
            'vivisect=cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Information Technology',
        'Topic :: Security',
        'Topic :: System :: Systems Administration',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: POSIX :: Linux',
    ],
)
