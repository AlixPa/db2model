from pydantic import BaseModel

from .table_import import TableImport


class TableDef(BaseModel):
    raw_str: str
    db_name: str
    schema_name: str | None
    table_name: str

    imports: list[TableImport] = list()
