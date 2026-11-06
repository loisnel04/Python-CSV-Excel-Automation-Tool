import pandas as pd
import pytest

from data_automation.reader import read_file


def test_read_csv(tmp_path):
    """Test reading a standard CSV file."""
    file_path = tmp_path / "customers.csv"

    file_path.write_text(
        "Name,Email,Age\n"
        "John Smith,john@mail.com,25\n"
        "Jane Doe,jane@mail.com,30\n",
        encoding="utf-8"
    )

    df = read_file(file_path)

    assert len(df) == 2
    assert list(df.columns) == ["Name", "Email", "Age"]
    assert df.iloc[0]["Name"] == "John Smith"


def test_read_csv_with_semicolon(tmp_path):
    """Test automatic detection of a semicolon separator."""
    file_path = tmp_path / "customers.csv"

    file_path.write_text(
        "Name;Email;Age\n"
        "John Smith;john@mail.com;25\n",
        encoding="utf-8"
    )

    df = read_file(file_path)

    assert len(df.columns) == 3
    assert "Email" in df.columns


def test_read_excel(tmp_path):
    """Test reading an Excel file."""
    file_path = tmp_path / "customers.xlsx"

    expected_df = pd.DataFrame({
        "Name": ["John Smith", "Jane Doe"],
        "Age": [25, 30]
    })

    expected_df.to_excel(file_path, index=False)

    df = read_file(file_path)

    assert len(df) == 2
    assert list(df.columns) == ["Name", "Age"]
    assert df.iloc[1]["Name"] == "Jane Doe"


def test_file_not_found():
    """Test that a missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        read_file("data/input/unknown.csv")


def test_unsupported_extension(tmp_path):
    """Test that unsupported file formats are rejected."""
    file_path = tmp_path / "customers.txt"
    file_path.write_text("Some text", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported file format"):
        read_file(file_path)


def test_path_is_directory(tmp_path):
    """Test that a directory cannot be read as a file."""
    with pytest.raises(ValueError, match="Path is not a file"):
        read_file(tmp_path)
