"""Export GraphQL schema to file for codegen without running server."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.chronos_graphql.schema import schema

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "src", "generated")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Export as SDL (Schema Definition Language)
sdl_path = os.path.join(OUTPUT_DIR, "schema.graphql")
with open(sdl_path, "w", encoding="utf-8") as f:
    f.write(schema.as_str())
print(f"Schema exported to {sdl_path}")

# Export as JSON for introspection
import json
from graphql import get_introspection_query, graphql_sync

json_path = os.path.join(OUTPUT_DIR, "schema.json")
introspection = graphql_sync(schema._schema, get_introspection_query()).data
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(introspection, f, indent=2)
print(f"Schema JSON exported to {json_path}")
