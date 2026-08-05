from setuptools import setup

setup(
    name="ntnu_inginious",
    version="0.2",
    description="Package containing patched LDAP auth module for NTNU system",
    url="https://algdat.idi.ntnu.no",
    author="Algdat team",
    author_email="algdat.idi.ntnu.no",
    license="AGPL",
    packages=["ntnu_inginious"],
    include_package_data=True,
    zip_safe=False,
)
