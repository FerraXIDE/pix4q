from setuptools import setup, find_packages

setup(
    name="pix4q",
    version="0.1.0",
    description="Natural command language for quantum image processing",
    author="FerraXIDE",
    license="Apache-2.0",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "qiskit>=1.0.0",
        "qiskit-aer>=0.14.0",
        "Pillow>=10.0.0",
        "numpy>=1.26.0",
        "scipy>=1.12.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Scientific/Engineering :: Physics",
    ],
)
