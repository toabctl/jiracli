Doing a release
===============
Some steps howto release an new version.

* Check that post release version bump happened (in `setup.cfg`)
* Create a signed git tag and push it::

    git tag -s 0.4.3
    git push --tags
* Upload to pypi::

    python setup.py sdist bdist_wheel upload

* Do post release version bump in `setup.cfg` and push it
