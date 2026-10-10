"""Upload naming: uploaded bills keep their original file name as bill ID."""
from __future__ import annotations

import tempfile
from pathlib import Path

from dashboard import io as ui_io


class FakeUpload:
    def __init__(self, name: str, data: bytes = b"x"):
        self.name = name
        self._data = data

    def getvalue(self) -> bytes:
        return self._data


def test_uploaded_to_temp_keeps_original_name():
    folder = Path(tempfile.mkdtemp(prefix="wtq_test_"))
    target = ui_io.uploaded_to_temp(FakeUpload("KESC_0006.png"), folder=folder)
    assert target.name == "KESC_0006.png"
    assert target.read_bytes() == b"x"


def test_uploaded_to_temp_sanitises_unsafe_names():
    folder = Path(tempfile.mkdtemp(prefix="wtq_test_"))
    target = ui_io.uploaded_to_temp(FakeUpload("My Bill (1).JPG"), folder=folder)
    assert target.name == "My_Bill_1.jpg"
    assert target.suffix == ".jpg"


def test_uploaded_to_temp_lowercases_extension_and_defaults():
    folder = Path(tempfile.mkdtemp(prefix="wtq_test_"))
    target = ui_io.uploaded_to_temp(FakeUpload("bill.PNG"), folder=folder)
    assert target.name == "bill.png"

    noext = ui_io.uploaded_to_temp(FakeUpload("justaname"), folder=folder)
    assert noext.name == "justaname.img" or noext.name.endswith(".img")


def test_same_name_twice_gets_unique_suffix():
    folder = Path(tempfile.mkdtemp(prefix="wtq_test_"))
    first = ui_io.uploaded_to_temp(FakeUpload("a.png", b"1"), folder=folder)
    second = ui_io.uploaded_to_temp(FakeUpload("a.png", b"2"), folder=folder)
    assert first != second
    assert first.read_bytes() == b"1"
    assert second.read_bytes() == b"2"