from setuptools import setup, find_packages

setup(
    name="gcs-deploy",  
    version="0.1.0",
    packages=find_packages(),  
    include_package_data=True,
    # install_requires=[
    # ],
    entry_points={
        "console_scripts": [
            "gcs-deploy=gcs_deploy.__main__:main",  
        ]
    },
    author="Felipe Jiménez Ibarra",
    description="Automated Globus Connect Server deployment utility",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.7",
)
