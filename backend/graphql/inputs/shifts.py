
import strawberry


@strawberry.input
class ScheduleTemplateItemInput:
    day_index: int
    shift_id: int | None = None


__all__ = ["ScheduleTemplateItemInput"]
