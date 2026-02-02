"""
Newsletter Platform tests.

Test Structure:
- conftest.py: Shared fixtures and pytest configuration
- test_imports.py: Module import validation (stable)
- test_config_base.py: Configuration tests (stable)
- test_schemas_base.py: Schema validation tests (stable)
- test_registration.py: Platform registration tests (stable)
- phase1/: Phase 1 stub behavior tests (will fail after Phase 10)
- integration/: Integration tests requiring running services

Running Tests:
    # All tests
    pytest app/platforms/newsletter/tests/

    # Only stable tests (skip phase1_stub)
    pytest app/platforms/newsletter/tests/ -m "not phase1_stub"

    # Only phase1 stub tests
    pytest app/platforms/newsletter/tests/ -m "phase1_stub"

    # Only integration tests
    pytest app/platforms/newsletter/tests/ -m "integration"

    # Skip integration tests
    pytest app/platforms/newsletter/tests/ -m "not integration"
"""
