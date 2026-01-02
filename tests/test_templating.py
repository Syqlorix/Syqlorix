from syqlorix.templating import *

def test_underscore_import():
    """
    Test that the underscore alias '_' is available and callable.
    This alias is used for the concise syntax: _('div.class')
    """
    assert callable(_)