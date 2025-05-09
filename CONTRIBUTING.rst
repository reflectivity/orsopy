.. highlight:: shell

============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/reflectivity/orsopy/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

orsopy could always use more documentation, whether as part of the
official orsopy docs, in docstrings, or even on the web in blog posts,
articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/reflectivity/orsopy/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
------------

Ready to contribute? Here's how to set up `orsopy` for local development.

1. Fork the `orsopy` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/orsopy.git

3. Install your local copy into a virtualenv. Assuming you have virtualenvwrapper installed, this is how you set up your fork for local development::

    $ mkvirtualenv orsopy
    $ cd orsopy/
    $ python setup.py develop

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. When you're done making changes, auto format the code and check that your changes pass the unit
   tests and confirms to PEP 8::

    $ black -l 120 orsopy tests
    $ isort -l 120 --lbt 1 orsopy tests
    $ flake8 --max-line-length=120 --ignore=F401,W503,E203 --count --show-source --statistics orsopy tests
    $ pytest

   To get flake8 and tox, just pip install them into your virtualenv.

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.

**Note**: It is easiest to run the automatic code formatting as git pre-commit hook for all changed files::

    #!C:/Program\ Files/Git/bin/sh.exe #<Windows, should be !/bin/bash on Linux/Mac
    for file in $(git diff --cached --name-only | grep -E '\.(py)$')
        do
            if [ -f "$file" ]; then
            echo "Reformat '$file'"
            black -l 120 "$file"
            isort -l 120 -l 120 --lbt 1 "$file"
            git add "$file"

            flake8 --max-line-length=120 --ignore=F401,W503,E203 "$file"
            if [ $? -ne 0 ]; then
                echo "flake8 failed on staged file '$file'"
                exit 1 # exit with failure status
            fi
        fi
    done

Pull Request Guidelines
-----------------------

Before you submit a pull request of your feature branch against the `main` branch of the `orsopy` repository,
check that it meets these guidelines:

1. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.rst.
2. The pull request should include tests for the new functionality. Run the tests in your local machine with `pytest`.
3. The pull request should work for Python 3.6, 3.7 and 3.8-latest, and for PyPy. To make sure that the tests pass
   for all supported Python versions, you can first create a pull
   request of your feature branch against the `main` branch _of your forked repository. If the Github actions
   pass, it is highly likely that the GitHub actions will also pass for the pull request against the `main` branch
   of the `orsopy` repository.

Tips
----

To run a subset of tests::

$ pytest tests.test_orsopy


Deploying
---------

A reminder for the maintainers on how to deploy:

1. Update schema file using `python tool/header_schema.py`
2. Update version string in `orsopy/__init__.py`
3. Make sure all your changes are committed (including an entry in `HISTORY.rst`)
4. Tag the commit with `vX.Y.Z`
5. Push your changes to your fork (e.g. `release` branch)
6. Create a pull requrest including the label `release` and get reviewer approval

GitHub actions will then deploy to PyPI if tests pass.
