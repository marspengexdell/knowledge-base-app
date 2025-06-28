"""Utilities for the generated gRPC modules.

The gRPC Python code produced by ``grpc_tools.protoc`` uses absolute imports
such as ``import inference_pb2``.  When these modules are loaded as part of the
``app.protos`` package this import would fail unless the current directory is
on ``sys.path``.  Docker builds run the stub generation step inside the image
so the resulting files live next to this ``__init__`` module.

To make the imports work both inside and outside the container we append this
directory to ``sys.path`` when the package is initialised.
"""

import os
import sys

_PROTO_DIR = os.path.dirname(__file__)
if _PROTO_DIR not in sys.path:
    sys.path.insert(0, _PROTO_DIR)
