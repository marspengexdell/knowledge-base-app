# Helper utilities for importing generated gRPC modules.

import os
import sys

_PROTO_DIR = os.path.dirname(__file__)
if _PROTO_DIR not in sys.path:
    sys.path.insert(0, _PROTO_DIR)
