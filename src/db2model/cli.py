import logging
from pathlib import Path

import typer
from sqlalchemy.engine import make_url

from db2model.config.settings import Db2ModelSettings, DbSettings, PathSettings
from db2model.generator.python import generate_python_models
from db2model.types import Language, SqlDialect

logger = logging.getLogger()
app = typer.Typer()


@app.command()
def hello():
    print(
        "This command is just here to prevent Typer to default generate command to empty command."
    )


@app.command()
def generate(
    lang: str = typer.Option(..., help="Language to generate. python, go, etc."),
    db_url: str = typer.Option(
        ..., help="Database url. Ex. postgresql://user:pass@localhost:5432/mydb"
    ),
    out_py: str = typer.Option(..., help="Output python models path. Ex. ./models"),
    out_raw: str = typer.Option(..., help="Output raws path. Ex. ./raw"),
    ignored_tables: list[str] = typer.Option(
        list(),
        help="List of tables to ignore. You can use this flag multiple times.",
    ),
    schemas: list[str] = typer.Option(
        list(),
        help="List of schemas to include if dialect is postgresql. You can use this flag multiple times.",
    ),
):
    """
    Generate models from the database.
    """
    try:
        url = make_url(db_url)
        dialect = SqlDialect(url.drivername.split("+")[0].upper())
        db_user = url.username
        db_password = url.password
        db_host = url.host
        db_port = url.port
        db_name = url.database
    except Exception as e:
        raise ValueError(f"Db url is not valid. {str(e)}.")

    if db_user is None:
        raise ValueError("Db user cannot be null")
    if db_password is None:
        raise ValueError("Db password cannot be null")
    if db_host is None:
        raise ValueError("Db host cannot be null")
    if db_port is None:
        raise ValueError("Db port cannot be null")
    if db_name is None:
        raise ValueError("Db name cannot be null")

    logger.info(f"Generating models for {dialect=}, {lang=}.")
    settings = Db2ModelSettings(
        path_settings=PathSettings(
            output_python_models_path=Path(out_py).resolve(),
            output_raw_path=Path(out_raw).resolve(),
        ),
        globally_ignored_tables=ignored_tables,
        schemas=schemas,
        db_settings=DbSettings(
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            db_name=db_name,
            default_schema="public",
            sql_dialect=dialect,
        ),
    )

    match Language(lang.upper()):
        case Language.PYTHON:
            generate_python_models(settings, logger)
        case _:
            raise ValueError(f"No support yet for the {lang=}")


def main():
    app()


if __name__ == "__main__":
    main()
