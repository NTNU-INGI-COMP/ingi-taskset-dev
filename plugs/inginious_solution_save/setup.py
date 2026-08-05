from setuptools import setup, find_packages

setup(
    name="inginious_solution_save",
    version="0.1dev0",
    description="Plugin to allow partial attempts to be saved temporarily in "
    "the users local storage",
    packages=find_packages(),
    include_package_data=True,
    author="Algdat team",
    author_email="algdat.idi.ntnu.no",
    license="AGPL",
)
