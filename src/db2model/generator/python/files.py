import shutil
from logging import Logger
from pathlib import Path

from sqlalchemy import MetaData, create_engine, text

from db2model.config.settings import Db2ModelSettings
from db2model.models import Table
from db2model.types import SqlDialect

from .table import _generate_table, _generate_table_code
from .templates import POSTGRES_SCHEMA_FILE
from .utils import _formate_code, _schema_to_ignore, _table_to_ignore


def generate_python_models(settings: Db2ModelSettings, logger: Logger) -> None:
    if settings.output_folder_path.exists():
        shutil.rmtree(settings.output_folder_path)
    settings.output_folder_path.mkdir(parents=True)

    base_code = "\n".join(
        [
            "from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass",
            "",
            "class Base(MappedAsDataclass, DeclarativeBase):",
            "    pass",
        ]
    )
    with open(settings.output_folder_path / "base.py", "w") as f:
        f.write(base_code)

    match settings.db_settings.sql_dialect:
        case SqlDialect.POSTGRESQL:
            engine = create_engine(settings.db_settings.db_url())
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT schema_name FROM information_schema.schemata")
                )
                schema_names: list[str] = [row[0] for row in result]

            models_output_folder_path = settings.output_folder_path / "models"
            models_output_folder_path.mkdir(parents=True)

            for schema_name in schema_names:
                if _schema_to_ignore(schema_name, settings):
                    logger.info(f"Ignored schema, {schema_name=}.")
                    continue

                engine = create_engine(
                    settings.db_settings.db_url(schema_name=schema_name)
                )
                metadata = MetaData()
                metadata.reflect(bind=engine)

                tables: list[Table] = list()
                for table_name, alc_table in metadata.tables.items():
                    if _table_to_ignore(schema_name, table_name, settings):
                        logger.info(f"Ignored table, {schema_name=}, {table_name=}.")
                        continue
                    tables.append(_generate_table(alc_table))

                if not tables:
                    logger.info(f"No tables to generate for {schema_name=}.")
                    continue

                code_blocks = [POSTGRES_SCHEMA_FILE]
                for table in tables:
                    code_blocks.append(
                        _generate_table_code(
                            schema_name, table, settings.db_settings.sql_dialect
                        )
                    )
                    logger.info(
                        f"Generated table model code block, {schema_name=}, {table.sql_name=}."
                    )
                with open(models_output_folder_path / f"{schema_name}.py", "w") as f:
                    f.write(_formate_code("\n".join(code_blocks)))
                logger.info(f"Generated schema models, {schema_name=}.")
        case _:
            raise ValueError(
                f"No support yet for the {settings.db_settings.sql_dialect=}"
            )
