from typing import Any

from pydantic import BaseModel


class Column(BaseModel):
    name: str
    nullable: bool
    is_primary_key: bool
    alchemy_type: Any
    python_type: str
    init: bool
    foreign_key_full_name: str | None

    def __lt__(self, other: "Column") -> bool:
        if other.name == "id":
            return False
        if self.nullable != other.nullable:
            return other.nullable
        return self.name < other.name
