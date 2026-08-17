"""Test-suite tenant mode.

``FORCE_DEFAULT_TENANT = True`` (default) makes the register/google-auth
endpoints reuse the seeded "default" tenant so most tests share one data
world. Isolation tests flip it to ``False`` so each registration creates a
real, separate tenant.
"""

FORCE_DEFAULT_TENANT = True
