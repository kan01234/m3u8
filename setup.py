from setuptools import setup, find_packages

setup(
    name='m3u8',
    version='1.0.0',
    description='A Python script to convert M3U8 files to MP4 format',
    url='https://github.com/kan01234/m3u8',
    author='kan01234',
    author_email='safghjkl@gmail.com',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    keywords='m3u8 mp4 ffmpeg',
    packages=find_packages(),
    python_requires='>=3.6',
    install_requires=[
        'requests',
        'tqdm',
        'atomic',
    ],
    entry_points={
        'console_scripts': [
            'm3u8=m3u8:main',
        ],
    },
)
