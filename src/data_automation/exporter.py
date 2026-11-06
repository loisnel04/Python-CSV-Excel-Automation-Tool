
from pathlib import Path

import pandas as pd


SUPPORTED_EXPORT_EXTENSIONS = {".csv", ".xlsx"}


def validate_output_path(
    file_path: str | Path,
    overwrite: bool = False,
) -> Path:
    """
    Validate and prepare an output file path.

    Creates the parent directory if it does not exist.

    Args:
        file_path: Destination file path.
        overwrite: Whether an existing file can be overwritten.

    Returns:
        Validated destination path.

    Raises:
        ValueError: If the extension is unsupported or the path
            points to an existing directory.
        FileExistsError: If the destination exists and overwrite
            is disabled.
    """
    path = Path(file_path)

    if path.suffix.lower() not in SUPPORTED_EXPORT_EXTENSIONS:
        raise ValueError(
            f"Unsupported export format: {path.suffix}. "
            f"Supported formats: "
            f"{', '.join(sorted(SUPPORTED_EXPORT_EXTENSIONS))}"
        )

    if path.exists() and path.is_dir():
        raise ValueError(f"Output path is a directory: {path}")

    if path.exists() and not overwrite:
        raise FileExistsError(
            f"Output file already exists: {path}. "
            "Set overwrite=True to replace it."
        )

    path.parent.mkdir(parents=True, exist_ok=True)

    return path


def export_csv(
    df: pd.DataFrame,
    file_path: str | Path,
    overwrite: bool = False,
    encoding: str = "utf-8-sig",
) -> Path:
    """
    Export a DataFrame to a CSV file.

    Args:
        df: DataFrame to export.
        file_path: Destination CSV path.
        overwrite: Whether an existing file can be overwritten.
        encoding: Output file encoding.

    Returns:
        Path to the exported file.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    path = validate_output_path(file_path, overwrite)

    if path.suffix.lower() != ".csv":
        raise ValueError("export_csv requires a .csv file extension.")

    df.to_csv(
        path,
        index=False,
        encoding=encoding,
    )

    return path


def export_excel(
    df: pd.DataFrame,
    file_path: str | Path,
    overwrite: bool = False,
    sheet_name: str = "Data",
) -> Path:
    """
    Export a DataFrame to an Excel file.

    Args:
        df: DataFrame to export.
        file_path: Destination Excel path.
        overwrite: Whether an existing file can be overwritten.
        sheet_name: Name of the Excel worksheet.

    Returns:
        Path to the exported file.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    if not isinstance(sheet_name, str) or not sheet_name.strip():
        raise ValueError("sheet_name must be a non-empty string.")

    if len(sheet_name) > 31:
        raise ValueError(
            "Excel worksheet names cannot exceed 31 characters."
        )

    if any(character in sheet_name for character in r"[]:*?/\\"):
        raise ValueError("Invalid character in Excel worksheet name.")

    path = validate_output_path(file_path, overwrite)

    if path.suffix.lower() != ".xlsx":
        raise ValueError("export_excel requires a .xlsx file extension.")

    df.to_excel(
        path,
        index=False,
        sheet_name=sheet_name,
        engine="openpyxl",
    )

    return path


def export_dataframe(
    df: pd.DataFrame,
    file_path: str | Path,
    overwrite: bool = False,
) -> Path:
    """
    Export a DataFrame using the format specified by the file extension.

    Supported formats:
        - CSV
        - XLSX

    Returns:
        Path to the exported file.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    path = Path(file_path)
    extension = path.suffix.lower()

    if extension == ".csv":
        return export_csv(
            df,
            path,
            overwrite=overwrite,
        )

    if extension == ".xlsx":
        return export_excel(
            df,
            path,
            overwrite=overwrite,
        )

    raise ValueError(
        f"Unsupported export format: {extension}. "
        f"Supported formats: "
        f"{', '.join(sorted(SUPPORTED_EXPORT_EXTENSIONS))}"
    )
