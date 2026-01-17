import logging
from pathlib import Path

import typer

from .config.settings import Db2ModelSettings, DbSettings
from .generator.python import generate_python_models
from .types import Language, SqlDialect

app = typer.Typer()
logger = logging.getLogger()


@app.command()
def generate(
    dialect: SqlDialect,
    language: Language,
    db_user: str,
    db_password: str,
    db_host: str,
    db_port: int,
    db_name: str,
    output_path: str,
    remove_empty_folders: bool = True,
):
    """
    Generate models from the database.
    """
    logger.info(f"Generating models for {dialect=}, {language=}.")

    settings = Db2ModelSettings(
        output_folder_path=Path(output_path).resolve(),
        remove_empty_folders=remove_empty_folders,
        db_names=[db_name],
        db_settings=DbSettings(
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            sql_dialect=dialect,
        ),
    )

    match language:
        case Language.PYTHON:
            generate_python_models(settings, logger)
        case _:
            raise ValueError(f"No support yet for the {language=}")


if __name__ == "__main__":
    app()
