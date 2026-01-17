from pydantic import BaseModel


class TableImport(BaseModel):
    schema_name: str | None
    table_name: str
