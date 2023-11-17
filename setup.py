from setuptools import setup

setup(
    name = 'testslurm',
    version = "0.1",
    description = "SLURM!",
    long_description = "SLURM!!!!.",
    long_description_content_type="text/plain",
    author = "Michael P. Lane",
    author_email = "mlanetheta@gmail.com",
    url = "https://github.com/automorphis/testslurm",
    package_dir = {"": "lib"},
    packages = [
        "testslurm"
    ],
    zip_safe = False
)