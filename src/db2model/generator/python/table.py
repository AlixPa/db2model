from sqlalchemy import Table as ALC_Table

from db2model.models import Table
from db2model.types import SqlDialect

from .column import _generate_column, _generate_column_code
from .utils import _formate_code, _python_table_name


def _generate_table(table: ALC_Table) -> Table:
    return Table(
        sql_name=table.name,
        python_name=_python_table_name(table.name[:-1]),
        columns=[_generate_column(col) for col in table.columns],
    )


def _generate_table_code(
    schema_name: str, table: Table, sql_dialect: SqlDialect
) -> str:
    lines = [
        f"class {table.python_name}(Base):",
        f'    __tablename__ = "{table.sql_name}"',
        f'    __table_args__ = {{"schema": "{schema_name}"}}',
    ]

    table.columns.sort()
    lines.extend(
        [("    " + _generate_column_code(col, sql_dialect)) for col in table.columns]
    )

    return _formate_code("\n".join(lines))
