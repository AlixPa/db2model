from pydantic import BaseModel

from .column import Column


class Table(BaseModel):
    sql_name: str
    python_name: str
    columns: list[Column]
