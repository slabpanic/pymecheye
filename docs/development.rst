Documentation and development
=============================

Build the documentation
-----------------------

Install the C++ SDK and select ``MECHEYE_SDK_ROOT`` as described in
:doc:`installation`. The documentation uses real imports, including dynamically
generated descriptors and containers. It does not construct or connect a camera.

.. code-block:: bash

   uv sync --locked --no-editable --group docs
   uv run --no-sync sphinx-build -n -W --keep-going -b html docs docs/_build/html

Open ``docs/_build/html/index.html``. Sphinx generates API indexes and autosummary
pages under ``docs/api/_generated/``; these are build products and are not committed.
Update docstrings in ``src/mecheye/`` to change the API reference. Dynamic value,
array, and descriptor documentation is attached by their factories.

The build treats warnings and unresolved references as errors and rejects missing
public docstrings. GitHub Actions runs the same build and saves the HTML as a
workflow artifact for review.

Read the Docs
-------------

The repository's ``.readthedocs.yaml`` uses Ubuntu and Python 3.12. It downloads
and verifies SDK 2.6.0 outside the checkout, builds the extension with the locked
``docs`` dependencies, and runs the strict Sphinx build. SDK files are not added
to the source distribution or HTML artifacts.

To activate hosted publishing once:

#. Sign in to `Read the Docs <https://app.readthedocs.org/>`_ using GitHub.
#. Install/authorize the Read the Docs GitHub App for ``slabpanic/pymecheye``.
#. Import that repository and set the project slug to ``pymecheye``.
#. Set the default branch to ``main`` and activate any release-tag versions you
   want to publish as stable documentation.
#. Enable pull request builds if previews are desired.

The GitHub integration triggers builds after pushes. The ``latest`` version
tracks the default branch; activated release versions can also be published.
The intended URL is ``https://pymecheye.readthedocs.io/en/latest/``. If the slug
is already taken, update the documentation links and ``html_baseurl`` to the
allocated project slug. No Read the Docs API token is required in GitHub Actions.

This setup uses the Read the Docs webhook integration for publication; the
GitHub Actions documentation job validates HTML and does not upload to a separate
hosting service. See the `Read the Docs integration guide
<https://docs.readthedocs.com/platform/stable/reference/git-integration.html>`_
for account and repository integration details.

Tests and coverage
------------------

.. code-block:: bash

   uv sync --locked --no-editable --group test
   uv run --no-sync python -B -m unittest discover -s tests
   uv run --no-sync coverage run -m unittest discover -s tests
   uv run --no-sync coverage report --fail-under=75

Tests cover SDK status and data operations with native containers and simulated
device responses. They do not require a camera. CI tests regular and free-threaded
Python, verifies source-distribution installation, and generates Python and C++
coverage reports. Native coverage requires GCC on Linux and the
``MECHEYE_ENABLE_COVERAGE`` CMake option. Codecov uploads use OIDC.

