from pathlib import Path
import pandas as pd

SUPPORTED_EXTENSIONS = {".csv", ".xlsx"}

def validate_file(file_path: str | Path) -> Path:
    """
    Validate that the input file exists and has a supported extension.
    Args:
        file_path: Path to the input file.
    Returns:
        Validated file path.
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file extension is unsupported.
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file format: {path.suffix}. "
            f"Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    return path


def read_csv(file_path: str | Path) -> pd.DataFrame:
    """
    Read a CSV file into a Pandas DataFrame.
    """
    path = validate_file(file_path)

    try:
        return pd.read_csv(
            path,
            sep=None,
            engine="python",
            encoding="utf-8-sig"
        )

    except UnicodeDecodeError:
        return pd.read_csv(
            path,
            sep=None,
            engine="python",
            encoding="latin-1"
        )


def read_excel(file_path: str | Path) -> pd.DataFrame:
    """
    Read an Excel file into a Pandas DataFrame.
    """
    path = validate_file(file_path)

    return pd.read_excel(path, engine="openpyxl")


def read_file(file_path: str | Path) -> pd.DataFrame:
    """
    Read a supported CSV or Excel file.

    Automatically selects the appropriate reader based on
    the file extension.
    """
    path = validate_file(file_path)

    extension = path.suffix.lower()

    if extension == ".csv":
        return read_csv(path)

    if extension == ".xlsx":
        return read_excel(path)

    raise ValueError(f"Unsupported file format: {extension}")
