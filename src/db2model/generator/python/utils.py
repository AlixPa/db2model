import autoflake
from black import FileMode, format_file_contents
from black.report import NothingChanged
from isort import code as isort_code

from db2model.config.settings import Db2ModelSettings


def _python_table_name(table_name: str):
    return "".join(w.capitalize() for w in table_name.split("_"))


def _formate_code(code: str) -> str:
    try:
        code = autoflake.fix_code(
            code, remove_unused_variables=True, remove_all_unused_imports=True
        )
        code = isort_code(code)
        try:
            code = format_file_contents(code, fast=False, mode=FileMode())
        except NothingChanged:
            pass
        return code
    except Exception:
        raise Exception(f"Could not parse: {code}")


def _join_imports_raw_text(raws: set[str]) -> str:
    return "\n".join(raws)
