import autoflake
from black import FileMode, format_file_contents
from black.report import NothingChanged
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
    try:
        code = format_file_contents(code, fast=False, mode=FileMode())
    except NothingChanged:
        pass
    return code


def _table_to_ignore(
    db_name: str, schema_name: str, table_name: str, settings: Db2ModelSettings
) -> bool:
    if table_name in settings.globally_ignored_tables:
        return True
    if table_name in settings.db_to_ignored_tables_map.get(db_name, list()):
        return True
    if table_name in settings.db_to_schemas_to_ignored_tables_map.get(
        db_name, dict()
    ).get(schema_name, list()):
        return True
    if "." in table_name:
        splits = table_name.split(".")
        if len(splits) > 2:
            raise RuntimeError(
                f"Got unexpected table name with multiple dots {table_name=}"
            )
        prefix, actual_table_name = splits[0], splits[1]
        if prefix not in (db_name, schema_name):
            return True
        if (
            prefix == db_name
            and actual_table_name
            in settings.db_to_ignored_tables_map.get(db_name, list())
        ):
            return True
        if (
            prefix == schema_name
            and actual_table_name
            in settings.db_to_schemas_to_ignored_tables_map.get(db_name, dict()).get(
                schema_name, list()
            )
        ):
            return True
    return False


def _schema_to_ignore(schema_name: str, settings: Db2ModelSettings) -> bool:
    return schema_name in settings.ignored_schemas
