from setuptools import setup

setup(
    name="feide_forward_auth",
    version="0.1",
    description="INGInious auth plugin trusting oauth2-proxy / Feide forward-auth headers",
    url="https://algdat.idi.ntnu.no",
    author="Algdat team",
    author_email="algdat.idi.ntnu.no",
    license="AGPL",
    packages=["feide_forward_auth"],
    include_package_data=True,
    zip_safe=False,
)
