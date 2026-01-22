import subprocess
from logging import Logger

from db2model.config import Db2ModelSettings
from db2model.types import Language, SqlDialect


def _run_sqlacodegen(settings: Db2ModelSettings, logger: Logger) -> None:
    match settings.db_settings.sql_dialect:
        case SqlDialect.POSTGRESQL:
            for schema_name in settings.schemas:
                db_url = settings.db_settings.db_url(
                    schema_name,
                )
                outfile = settings.path_settings.raw_filepath(
                    Language.PYTHON,
                    settings.db_settings.sql_dialect,
                    schema_name,
                )
                logger.info(f"Generating raw schema for python on {schema_name=}")
                subprocess.run(
                    [
                        "sqlacodegen",
                        db_url,
                        "--schema",
                        schema_name,
                        "--outfile",
                        str(outfile),
                    ],
                    check=True,
                )
        case _:
            raise ValueError(
                f"No support yet for the {settings.db_settings.sql_dialect=}"
            )
