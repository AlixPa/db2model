import shutil
from logging import Logger
from pathlib import Path

from sqlalchemy import MetaData, create_engine, text

from db2model.config.settings import Db2ModelSettings
from db2model.models import Table
from db2model.types import SqlDialect

from .table import _generate_table, _generate_table_code
from .templates import POSTGRES_TABLE_FILE_TEMPLATE
from .utils import _formate_code, _schema_to_ignore, _table_to_ignore


def _generate_empty_init_file(output_path: Path) -> None:
    with open(output_path / "__init__.py", "w") as f:
        f.write("__all__ = []\n")


def _generate_base_file(output_path: Path) -> None:
    base_code = "\n".join(
        [
            "from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass",
            "",
            "class Base(MappedAsDataclass, DeclarativeBase):",
            "    pass",
            "",
        ]
    )
    with open(output_path / "base.py", "w") as f:
        f.write(base_code)


def _generate_init_file(tables: list[Table], output_folder_path: Path) -> None:
    lines: list[str] = []
    for table in tables:
        lines.append(f"from .{table.filename} import {table.python_name}")

    lines.append("__all__ = [")

    for table in tables:
        lines.append(f'"{table.python_name}",')

    lines.append("]")

    code = "\n".join(lines)

    with open(output_folder_path / "__init__.py", "w") as f:
        f.write(_formate_code(code))


def generate_python_models(settings: Db2ModelSettings, logger: Logger) -> None:
    settings.output_folder_path.mkdir(parents=True, exist_ok=True)

    _generate_empty_init_file(settings.output_folder_path)
    _generate_base_file(settings.output_folder_path)

    match settings.db_settings.sql_dialect:
        case SqlDialect.POSTGRESQL:
            for db_name in settings.db_names:
                db_table_created_cnt = 0

                db_output_folder_path = settings.output_folder_path / db_name
                if db_output_folder_path.exists():
                    shutil.rmtree(db_output_folder_path)
                db_output_folder_path.mkdir(parents=True, exist_ok=True)

                _generate_empty_init_file(db_output_folder_path)

                engine = create_engine(settings.db_settings.db_url(db_name))
                with engine.connect() as conn:
                    result = conn.execute(
                        text("SELECT schema_name FROM information_schema.schemata")
                    )
                    schema_names: list[str] = [row[0] for row in result]

                for schema_name in schema_names:
                    if _schema_to_ignore(schema_name, settings):
                        logger.info(f"Ignored schema, {schema_name=}.")
                        continue

                    engine = create_engine(
                        settings.db_settings.db_url(db_name, schema_name=schema_name)
                    )
                    metadata = MetaData()
                    metadata.reflect(bind=engine)

                    schema_tables: list[Table] = list()
                    for table_name, alc_table in metadata.tables.items():
                        if _table_to_ignore(db_name, schema_name, table_name, settings):
                            logger.info(
                                f"Ignored table, {schema_name=}, {table_name=}."
                            )
                            continue
                        schema_tables.append(_generate_table(alc_table))

                    db_table_created_cnt += len(schema_tables)
                    schema_output_folder_path = db_output_folder_path / schema_name
                    schema_output_folder_path.mkdir(parents=True)
                    for table in schema_tables:
                        with open(
                            schema_output_folder_path / f"{table.filename}.py", "w"
                        ) as f:
                            f.write(
                                _formate_code(
                                    "\n".join(
                                        [
                                            POSTGRES_TABLE_FILE_TEMPLATE,
                                            _generate_table_code(
                                                schema_name,
                                                table,
                                                settings.db_settings.sql_dialect,
                                            ),
                                        ]
                                    )
                                )
                            )
                        logger.info(
                            f"Generated table model code block, {schema_name=}, {table.sql_name=}."
                        )
                    _generate_init_file(schema_tables, schema_output_folder_path)
                    logger.info(
                        f"Generated schema models, {schema_name=}, {len(schema_tables)=}."
                    )

                    if not schema_tables and settings.remove_empty_folders:
                        shutil.rmtree(schema_output_folder_path)
                        logger.info(
                            f"No tables generated for {schema_name=}, removing folder."
                        )

                if not db_table_created_cnt and settings.remove_empty_folders:
                    shutil.rmtree(db_output_folder_path)
                    logger.info(f"No tables generated for {db_name=}, removing folder.")
        case _:
            raise ValueError(
                f"No support yet for the {settings.db_settings.sql_dialect=}"
            )
