from pydantic import BaseModel

from .column import Column


class Table(BaseModel):
    sql_name: str
    python_name: str
    filename: str
    columns: list[Column]
