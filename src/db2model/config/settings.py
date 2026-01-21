import shutil
from pathlib import Path

from pydantic.fields import PrivateAttr
from pydantic_settings import BaseSettings, SettingsConfigDict

from db2model.types import Language, SqlDialect


class DbSettings(BaseSettings):
    model_config = SettingsConfigDict(frozen=True)

    user: str
    password: str
    host: str
    port: int

    sql_dialect: SqlDialect

    # Postgresql specific, usually "public"
    default_schema: str | None = None

    def db_url(self, db_name: str, schema_name: str | None = None) -> str:
        match self.sql_dialect:
            case SqlDialect.POSTGRESQL:
                return (
                    "postgresql+psycopg"
                    + f"://{self.user}:{self.password}@{self.host}:{self.port}/{db_name}"
                    + (
                        f"?options=-csearch_path={schema_name},public"
                        if schema_name
                        else ""
                    )
                )
            case _:
                raise ValueError(f"No support yet for the {sql_dialect=}")


class PathSettings(BaseSettings):
    model_config = SettingsConfigDict(frozen=True)

    output_folder_root_path: Path

    @property
    def raw_path(self) -> Path:
        path = self.output_folder_root_path / "raw"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def python_models_path(self) -> Path:
        path = self.output_folder_root_path / "python" / "models"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def raw_filepath(
        self,
        language: Language,
        sql_dialect: SqlDialect,
        db_name: str,
        schema_name: str | None = None,
    ) -> Path:
        match sql_dialect:
            case SqlDialect.POSTGRESQL:
                if not schema_name:
                    raise RuntimeError(
                        "Schema name must be provided when using postgresql."
                    )
                folder_path = self.raw_path / db_name
                folder_path.mkdir(parents=True, exist_ok=True)
                base_filename = schema_name
            case _:
                raise ValueError(f"No support yet for the {sql_dialect=}")

        match language:
            case Language.PYTHON:
                return folder_path / f"{base_filename}.py"
            case _:
                raise ValueError(f"No support yet for the {language=}")

    def table_filepath(
        self,
        language: Language,
        sql_dialect: SqlDialect,
        db_name: str,
        table_name: str,
        schema_name: str | None = None,
    ):
        match sql_dialect:
            case SqlDialect.POSTGRESQL:
                if not schema_name:
                    raise RuntimeError(
                        "Schema name must be provided when using postgresql."
                    )
                base_folder_path = self.python_models_path / db_name / schema_name
            case _:
                raise ValueError(f"No support yet for the {sql_dialect=}")

        match language:
            case Language.PYTHON:
                folder_path = self.python_models_path / base_folder_path
                folder_path.mkdir(parents=True, exist_ok=True)
                return folder_path / f"{table_name}.py"
            case _:
                raise ValueError(f"No support yet for the {language=}")


class Db2ModelSettings(BaseSettings):
    model_config = SettingsConfigDict(frozen=True)

    path_settings: PathSettings

    db_names: list[str]
    db_settings: DbSettings

    init_false_column_names: list[str] = list()

    globally_ignored_tables: list[str] = list()
    db_to_ignored_tables_map: dict[str, list[str]] = dict()

    # postgres specific
    db_to_schemas: dict[str, list[str]] = dict()
    db_to_schemas_to_ignored_tables_map: dict[str, dict[str, list[str]]] = dict()
    globally_ignored_schemas: list[str] = list()
