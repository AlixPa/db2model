from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from db2model.types import SqlDialect


class DbSettings(BaseSettings):
    model_config = SettingsConfigDict(frozen=True)

    user: str
    password: str
    host: str
    port: int
    db_name: str

    sql_dialect: SqlDialect

    def db_url(self, schema_name: str | None = None) -> str:
        match self.sql_dialect:
            case SqlDialect.POSTGRESQL:
                return (
                    "postgresql+psycopg"
                    + f"://{self.user}:{self.password}@{self.host}:{self.port}/{self.db_name}"
                    + (
                        f"?options=-csearch_path={schema_name},public"
                        if schema_name is not None
                        else ""
                    )
                )
            case _:
                raise ValueError(f"No support yet for the {sql_dialect=}")


class Db2ModelSettings(BaseSettings):
    model_config = SettingsConfigDict(frozen=True)

    output_folder_path: Path
    db_settings: DbSettings
    globally_ignored_tables: list[str] = list()

    # postgres specific
    schema_name_to_ignored_tables_map: dict[str, list[str]] = dict()
    ignored_schemas: list[str] = list()
