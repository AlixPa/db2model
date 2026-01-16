import autoflake
from black import FileMode, format_file_contents
from isort import code as isort_code
from sqlalchemy import Column as ALC_Column

from db2model.config.settings import Db2ModelSettings
from db2model.config.type_map import TYPE_MAP
from db2model.types import SqlDialect


def _python_type(col: ALC_Column):
    for sa_type, py in TYPE_MAP[SqlDialect.POSTGRESQL]:
        if isinstance(col.type, sa_type):
            return py
    return "Any"


def _python_table_name(table_name: str):
    return "".join(w.capitalize() for w in table_name.split("_"))


def _formate_code(code: str) -> str:
    code = autoflake.fix_code(
        code, remove_unused_variables=True, remove_all_unused_imports=True
    )
    code = isort_code(code)
    code = format_file_contents(code, fast=False, mode=FileMode())
    return code


def _table_to_ignore(
    schema_name: str, table_name: str, settings: Db2ModelSettings
) -> bool:
    if table_name in settings.globally_ignored_tables:
        return True
    if table_name in settings.schema_name_to_ignored_tables_map.get(schema_name, []):
        return True
    if "." in table_name and table_name.split(".")[0] != schema_name:
        return True
    return False


def _schema_to_ignore(schema_name: str, settings: Db2ModelSettings) -> bool:
    return schema_name in settings.ignored_schemas
