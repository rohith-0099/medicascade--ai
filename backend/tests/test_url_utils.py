from utils.url_utils import format_url


def test_empty_path_returns_empty_string():
    assert format_url("") == ""
    assert format_url(None) == ""


def test_outputs_relative_path_gets_root_slash():
    assert format_url("outputs/cases/abc/report.pdf") == "/outputs/cases/abc/report.pdf"


def test_absolute_path_truncated_to_outputs_segment():
    src = "/home/user/project/backend/outputs/cases/abc/report.pdf"
    assert format_url(src) == "/outputs/cases/abc/report.pdf"


def test_windows_separators_normalised():
    assert format_url("outputs\\cases\\abc\\report.pdf") == "/outputs/cases/abc/report.pdf"


def test_unrelated_path_served_from_root():
    assert format_url("uploads/file.pdf") == "/uploads/file.pdf"
