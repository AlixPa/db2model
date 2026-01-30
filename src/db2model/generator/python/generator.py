from logging import Logger

from db2model.config import Db2ModelSettings
from db2model.models import TableDef
from db2model.types import Language, SqlDialect

from .files import _code_base_file, _generate_all_init_files
from .parser import _parse_file
from .raw import _run_sqlacodegen
from .table import (
    _fill_table_imports,
    _fusion_tables,
    _get_python_name_to_table_def_map,
    _get_table_code,
    _group_table_per_name,
    _set_table_default_none,
    _set_table_inits_false,
)
from .utils import _formate_code, _join_imports_raw_text


def generate_python_models(settings: Db2ModelSettings, logger: Logger) -> None:
    _run_sqlacodegen(settings, logger)
    with open(settings.path_settings.python_models_path / "base.py", "w") as f:
        f.write(_formate_code(_code_base_file()))
    with open(settings.path_settings.python_models_path / "__init__.py", "w") as f:
        f.write(_formate_code("__all__ = []\n"))

    imports_raw_texts: set[str] = {"from typing import TYPE_CHECKING"}
    db_tables_def: list[TableDef] = list()

    match settings.db_settings.sql_dialect:
        case SqlDialect.POSTGRESQL:
            imports_raw_texts.add("from ..base import Base")
            for schema_name in settings.schemas:
                raw_filepath = settings.path_settings.raw_filepath(
                    Language.PYTHON,
                    settings.db_settings.sql_dialect,
                    schema_name,
                )

                parsed_file = _parse_file(
                    raw_filepath,
                    settings.db_settings.sql_dialect,
                )
                if parsed_file is None:
                    logger.info(f"No tables found in {schema_name=}, skipping.")
                    continue
                imports_raw_text, tables_def = parsed_file

                final_tables_def: list[TableDef] = list()
                for table_def in tables_def:
                    if (table_def.table_name in settings.globally_ignored_tables) or (
                        table_def.table_name
                        in settings.schema_to_ignored_tables_map.get(
                            schema_name, list()
                        )
                    ):
                        logger.info(
                            f"Ignoring table {schema_name=}, {table_def.table_name=}."
                        )
                        continue
                    final_tables_def.append(table_def)

                if not final_tables_def:
                    logger.info(f"All tables were ignores for {schema_name=}.")
                    continue

                imports_raw_texts.add(imports_raw_text)
                db_tables_def.extend(final_tables_def)
        case _:
            raise ValueError(
                f"No support yet for the {settings.db_settings.sql_dialect=}"
            )

    final_imports_raw_text = _join_imports_raw_text(imports_raw_texts)
    name_to_tables_def_map = _group_table_per_name(db_tables_def)
    db_all_tables_def = [
        _fusion_tables(tn, td) for tn, td in name_to_tables_def_map.items()
    ]
    python_name_to_table_def_map = _get_python_name_to_table_def_map(db_all_tables_def)

    _generate_all_init_files(
        settings.path_settings.python_models_path,
        db_all_tables_def,
        settings.db_settings.sql_dialect,
    )

    for table_def in db_all_tables_def:
        _fill_table_imports(table_def, python_name_to_table_def_map)
        _set_table_inits_false(table_def, settings.init_false_column_names)
        _set_table_default_none(table_def)

        code = _get_table_code(
            final_imports_raw_text,
            table_def,
            settings.db_settings.sql_dialect,
            settings.db_settings.default_schema,
        )

        with open(
            settings.path_settings.table_filepath(
                language=Language.PYTHON,
                sql_dialect=settings.db_settings.sql_dialect,
                table_name=table_def.table_name,
                schema_name=table_def.schema_name,
            ),
            "w",
        ) as f:
            f.write(_formate_code(code))
