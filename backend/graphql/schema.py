import strawberry

from backend.graphql.queries import Query
from backend.graphql.mutations import Mutation
from backend.graphql.module_middleware import ModuleGuardMiddleware

schema = strawberry.Schema(
    query=Query, 
    mutation=Mutation,
    extensions=[ModuleGuardMiddleware]
)
