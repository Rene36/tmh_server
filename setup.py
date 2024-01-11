# stdlib
import os
from setuptools import find_packages, setup


def read(file_name: str):
    """
    Utility function to read the README file.
    Used for the long_description.  
    """
    return open(os.path.join(os.path.dirname(__file__), file_name),
                encoding="utf-8").read()


with open("requirements.txt", encoding="utf-8") as f:
    all_reqs = f.read().split("\n")
install_requires = [x.strip() for x in all_reqs if "git+" not in x]
dependency_links = [x.strip().replace("git+", "")
                    for x in all_reqs if x.startswith("git+")]

setup(name="tmh_server",
      version="1.0.0",
      author="René Schwermer",
      author_email="rene.schwermer@tum.de",
      description="Package to extract data of curtailed power and energy from different sources.",
      license="proprietary",
      keywords="API, data processing, power crutailments, database",
      url="https://github.com/Rene36/tmh_server",
      packages=find_packages(),
      install_requires=install_requires,
      dependency_links=dependency_links,
      long_description=read("README.md"),
      classifiers=["Development Status :: 3 Alpha",
                   "License :: Other/Proprietary License",
                   "Operating System :: Linux",
                   "Programming Language :: Python",
                   "Programming Language :: Python 3",
                   "Topic :: Scientific/Engineering"]
      )
