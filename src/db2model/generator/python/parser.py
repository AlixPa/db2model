import re
from pathlib import Path

from db2model.models import TableDef
from db2model.types import SqlDialect

from .constants import EMPTY_FILE_TEMPLATE


def _parse_table(raw: str, sql_dialect: SqlDialect) -> TableDef:
    name_match = re.search(r"__tablename__\s*=\s*['\"]([^'\"]+)['\"]", raw)
    if not name_match:
        raise ValueError(
            f"Problem during python file generation, could not find __tablename__. {raw=}"
        )

    match sql_dialect:
        case SqlDialect.POSTGRESQL:
            schema_match = re.search(r"['\"]schema['\"]\s*:\s*['\"]([^'\"]+)['\"]", raw)
            if schema_match:
                schema_name = schema_match.group(1)
            else:
                schema_name = "public"
        case _:
            raise ValueError(f"No support yet for the {sql_dialect=}")

    return TableDef(
        raw_str=raw,
        table_name=name_match.group(1),
        schema_name=schema_name,
    )


def _clean_table_raw(raw_str: str) -> str:
    all_lines = [line for line in raw_str.split("\n") if line.strip()]
    lines = [all_lines[0]]
    for line in all_lines[1:]:
        if line.startswith("    "):
            lines.append(line)
        else:
            break
    return "\n".join(lines)


def _parse_file(
    filepath: Path, sql_dialect: SqlDialect
) -> tuple[str, list[TableDef]] | None:
    """(imports_raw_text, list_tables), None if file has no tables"""

    with open(filepath, "r") as f:
        full_text = f.read()
    base_class_text = """class Base(DeclarativeBase):
    pass"""
    splits = full_text.split(base_class_text)
    if len(splits) != 2:
        if full_text == EMPTY_FILE_TEMPLATE:
            return None
        raise ValueError(
            f"Problem during python file generation, could not find class Bass definition. {full_text=}"
        )
    imports_raw_text, classes_raw_text = splits[0], splits[1]
    classes_raw_text = "\n" + classes_raw_text.strip()
    classes_splits = classes_raw_text.split("\nclass ")
    tables_def: list[TableDef] = list()
    for class_split in classes_splits:
        if not class_split:
            continue
        class_split = "\nclass " + class_split
        clean_str = _clean_table_raw(class_split)
        if clean_str:
            tables_def.append(_parse_table(clean_str, sql_dialect))
    return imports_raw_text, tables_def
