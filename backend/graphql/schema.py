import sys
import strawberry
import traceback
import os
from backend.graphql.queries import Query
from backend.graphql.mutations import Mutation
from backend.graphql.module_middleware import ModuleGuardMiddleware
from backend.graphql.error_handler import ChronosErrorExtension
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    schema = strawberry.Schema(
        query=Query, 
        mutation=Mutation,
        extensions=[ModuleGuardMiddleware, ChronosErrorExtension]
    )
except Exception as e:
    print(f"Error creating schema: {e}", file=__import__('sys').stderr)
    traceback.print_exc()
    raise
