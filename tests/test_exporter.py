
import pandas as pd
import pytest

from data_automation.exporter import (
    export_csv,
    export_excel,
    export_dataframe,
    validate_output_path,
)


@pytest.fixture
def sample_dataframe():
    return pd.DataFrame({
        "name": ["John Smith", "Jane Doe"],
        "email": ["john@mail.com", "jane@mail.com"],
        "age": [25, 30],
    })


# ---------------------------------------------------------
# CSV export
# ---------------------------------------------------------

def test_export_csv(sample_dataframe, tmp_path):
    output_path = tmp_path / "output" / "customers.csv"

    result = export_csv(sample_dataframe, output_path)

    assert result == output_path
    assert output_path.exists()

    exported_df = pd.read_csv(output_path, encoding="utf-8-sig")

    pd.testing.assert_frame_equal(
        exported_df,
        sample_dataframe,
    )


def test_export_csv_does_not_export_index(
    sample_dataframe,
    tmp_path,
):
    output_path = tmp_path / "customers.csv"

    export_csv(sample_dataframe, output_path)

    exported_df = pd.read_csv(output_path)

    assert "Unnamed: 0" not in exported_df.columns


# ---------------------------------------------------------
# Excel export
# ---------------------------------------------------------

def test_export_excel(sample_dataframe, tmp_path):
    output_path = tmp_path / "output" / "customers.xlsx"

    result = export_excel(sample_dataframe, output_path)

    assert result == output_path
    assert output_path.exists()

    exported_df = pd.read_excel(output_path)

    pd.testing.assert_frame_equal(
        exported_df,
        sample_dataframe,
    )


def test_export_excel_custom_sheet_name(
    sample_dataframe,
    tmp_path,
):
    output_path = tmp_path / "customers.xlsx"

    export_excel(
        sample_dataframe,
        output_path,
        sheet_name="Customer Data",
    )

    exported_df = pd.read_excel(
        output_path,
        sheet_name="Customer Data",
    )

    pd.testing.assert_frame_equal(
        exported_df,
        sample_dataframe,
    )


# ---------------------------------------------------------
# Automatic format selection
# ---------------------------------------------------------

def test_export_dataframe_csv(sample_dataframe, tmp_path):
    output_path = tmp_path / "customers.csv"

    result = export_dataframe(sample_dataframe, output_path)

    assert result == output_path
    assert output_path.exists()


def test_export_dataframe_excel(sample_dataframe, tmp_path):
    output_path = tmp_path / "customers.xlsx"

    result = export_dataframe(sample_dataframe, output_path)

    assert result == output_path
    assert output_path.exists()


# ---------------------------------------------------------
# Output path validation
# ---------------------------------------------------------

def test_create_output_directory(tmp_path):
    output_path = tmp_path / "new_folder" / "output.csv"

    result = validate_output_path(output_path)

    assert result == output_path
    assert output_path.parent.exists()


def test_prevent_overwriting_existing_file(tmp_path):
    output_path = tmp_path / "customers.csv"
    output_path.write_text("existing content", encoding="utf-8")

    with pytest.raises(FileExistsError):
        validate_output_path(output_path)


def test_allow_overwriting_existing_file(tmp_path):
    output_path = tmp_path / "customers.csv"
    output_path.write_text("existing content", encoding="utf-8")

    result = validate_output_path(
        output_path,
        overwrite=True,
    )

    assert result == output_path


def test_reject_unsupported_extension(tmp_path):
    output_path = tmp_path / "customers.txt"

    with pytest.raises(ValueError, match="Unsupported export format"):
        export_dataframe(
            pd.DataFrame({"name": ["John"]}),
            output_path,
        )


def test_reject_csv_export_with_excel_extension(
    sample_dataframe,
    tmp_path,
):
    output_path = tmp_path / "customers.xlsx"

    with pytest.raises(ValueError, match="requires a .csv"):
        export_csv(sample_dataframe, output_path)


def test_reject_excel_export_with_csv_extension(
    sample_dataframe,
    tmp_path,
):
    output_path = tmp_path / "customers.csv"

    with pytest.raises(ValueError, match="requires a .xlsx"):
        export_excel(sample_dataframe, output_path)


# ---------------------------------------------------------
# Input validation
# ---------------------------------------------------------

def test_reject_invalid_dataframe(tmp_path):
    with pytest.raises(TypeError, match="pandas DataFrame"):
        export_dataframe(
            ["John", "Jane"],
            tmp_path / "customers.csv",
        )


def test_reject_empty_sheet_name(tmp_path):
    df = pd.DataFrame({"name": ["John"]})

    with pytest.raises(ValueError, match="non-empty"):
        export_excel(
            df,
            tmp_path / "customers.xlsx",
            sheet_name="",
        )


def test_reject_long_sheet_name(tmp_path):
    df = pd.DataFrame({"name": ["John"]})

    with pytest.raises(ValueError, match="31 characters"):
        export_excel(
            df,
            tmp_path / "customers.xlsx",
            sheet_name="A" * 32,
        )


def test_reject_invalid_sheet_name_character(tmp_path):
    df = pd.DataFrame({"name": ["John"]})

    with pytest.raises(ValueError, match="Invalid character"):
        export_excel(
            df,
            tmp_path / "customers.xlsx",
            sheet_name="Customer/Data",
        )


def test_export_empty_dataframe(tmp_path):
    df = pd.DataFrame(columns=["name", "age"])
    output_path = tmp_path / "empty.csv"

    export_csv(df, output_path)

    exported_df = pd.read_csv(output_path)

    assert list(exported_df.columns) == ["name", "age"]
    assert len(exported_df) == 0
