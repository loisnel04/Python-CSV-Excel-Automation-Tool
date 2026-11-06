
import pandas as pd

from data_automation import main as main_module


def test_get_input_files(tmp_path, monkeypatch):
    """Return only supported files from the input directory."""

    (tmp_path / "customers.csv").touch()
    (tmp_path / "orders.xlsx").touch()
    (tmp_path / "notes.txt").touch()
    (tmp_path / "subfolder").mkdir()

    monkeypatch.setattr(main_module, "INPUT_DIR", tmp_path)

    files = main_module.get_input_files()

    assert len(files) == 2
    assert {file.name for file in files} == {
        "customers.csv",
        "orders.xlsx",
    }


def test_merge_compatible_files(tmp_path, monkeypatch, capsys):
    """Merge compatible files and generate output reports."""

    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"

    input_dir.mkdir()

    file_1 = input_dir / "customers_1.csv"
    file_2 = input_dir / "customers_2.csv"

    file_1.touch()
    file_2.touch()

    dataframe_1 = pd.DataFrame({
        "Customer ID": [1, 2],
        "First Name": ["Alice", "Bob"],
        "Email": ["alice@example.com", "bob@example.com"],
    })

    dataframe_2 = pd.DataFrame({
        "Email": ["bob@example.com", "charlie@example.com"],
        "First Name": ["Bob", "Charlie"],
        "Customer ID": [2, 3],
    })

    def mock_read_file(file_path):
        if file_path.name == "customers_1.csv":
            return dataframe_1.copy()

        return dataframe_2.copy()

    monkeypatch.setattr(main_module, "INPUT_DIR", input_dir)
    monkeypatch.setattr(main_module, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(main_module, "read_file", mock_read_file)

    main_module.run_merge_processing()

    cleaned_file = output_dir / "merged_cleaned.xlsx"
    report_file = output_dir / "merged_quality_report.xlsx"

    assert cleaned_file.exists()
    assert report_file.exists()

    cleaned_df = pd.read_excel(cleaned_file)

    assert len(cleaned_df) == 3
    assert list(cleaned_df.columns) == [
        "customer_id",
        "first_name",
        "email",
    ]

    output = capsys.readouterr().out

    assert "[SUCCESS] Merge processing completed." in output
    assert "Original rows:    4" in output
    assert "Cleaned rows:     3" in output


def test_merge_rejects_incompatible_schemas(
    tmp_path,
    monkeypatch,
    capsys,
):
    """Cancel merging when input schemas are incompatible."""

    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"

    input_dir.mkdir()

    (input_dir / "file_1.csv").touch()
    (input_dir / "file_2.csv").touch()

    dataframe_1 = pd.DataFrame({
        "Customer ID": [1],
        "Name": ["Alice"],
    })

    dataframe_2 = pd.DataFrame({
        "Customer ID": [2],
        "Email": ["bob@example.com"],
    })

    def mock_read_file(file_path):
        if file_path.name == "file_1.csv":
            return dataframe_1.copy()

        return dataframe_2.copy()

    monkeypatch.setattr(main_module, "INPUT_DIR", input_dir)
    monkeypatch.setattr(main_module, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(main_module, "read_file", mock_read_file)

    main_module.run_merge_processing()

    output = capsys.readouterr().out

    assert "Incompatible schema" in output
    assert "Merge cancelled" in output
    assert not list(output_dir.glob("*"))


def test_merge_requires_at_least_two_files(
    tmp_path,
    monkeypatch,
    capsys,
):
    """Reject merge processing when only one file is available."""

    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"

    input_dir.mkdir()
    (input_dir / "customers.csv").touch()

    monkeypatch.setattr(main_module, "INPUT_DIR", input_dir)
    monkeypatch.setattr(main_module, "OUTPUT_DIR", output_dir)

    main_module.run_merge_processing()

    output = capsys.readouterr().out

    assert "requires at least two" in output
    assert not output_dir.exists()


def test_merge_handles_read_error(
    tmp_path,
    monkeypatch,
    capsys,
):
    """Handle file reading errors without crashing."""

    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"

    input_dir.mkdir()

    (input_dir / "file_1.csv").touch()
    (input_dir / "file_2.csv").touch()

    def mock_read_file(file_path):
        raise ValueError("Invalid file content.")

    monkeypatch.setattr(main_module, "INPUT_DIR", input_dir)
    monkeypatch.setattr(main_module, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(main_module, "read_file", mock_read_file)

    main_module.run_merge_processing()

    output = capsys.readouterr().out

    assert "Merge processing failed" in output
    assert "Invalid file content" in output
    assert not list(output_dir.glob("*"))
