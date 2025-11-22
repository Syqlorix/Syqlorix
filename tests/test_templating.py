
from syqlorix.templating import *

def test_underscore_import():
    # This test will fail if '_' is not in __all__
    assert callable(_)
