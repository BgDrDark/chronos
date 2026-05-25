import os
import sys
import traceback

import strawberry

from backend.graphql.error_handler import ChronosErrorExtension
from backend.graphql.module_middleware import ModuleGuardMiddleware
from backend.graphql.mutations import Mutation
from backend.graphql.queries import Query

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        extensions=[ModuleGuardMiddleware, ChronosErrorExtension],
    )
except Exception as e:
    print(f"Error creating schema: {e}", file=__import__("sys").stderr)
    traceback.print_exc()
    raise
