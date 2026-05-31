from typing import Any

from pydantic import BaseModel, ConfigDict


class CustomBaseModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        ser_json_timedelta="iso8601",
        validate_default=False,
    )

    def model_dump(self, **kwargs) -> dict[str, Any]:
        kwargs.setdefault("mode", "json")
        return super().model_dump(**kwargs)
