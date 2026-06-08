"""Export GraphQL schema to file for codegen without running server."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.graphql.schema import schema

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "src", "generated")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Export as SDL (Schema Definition Language)
sdl_path = os.path.join(OUTPUT_DIR, "schema.graphql")
with open(sdl_path, "w", encoding="utf-8") as f:
    f.write(schema.as_str())
print(f"Schema exported to {sdl_path}")

# Export as JSON for introspection
import json
json_path = os.path.join(OUTPUT_DIR, "schema.json")
json_schema = schema._schema.schema_dump()
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(json_schema, f)
print(f"Schema JSON exported to {json_path}")
