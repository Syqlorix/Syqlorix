def test_package_can_be_imported():
    """
    This is a simple smoke test. It confirms that the 'syqlorix' package
    can be successfully imported without raising any errors.
    """
    try:
        import syqlorix
    except ImportError as e:
        assert False, f"Failed to import the syqlorix package: {e}"
    except Exception as e:
        assert False, f"An unexpected error occurred during import: {e}"

    assert True