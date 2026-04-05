"""Tests for cloud upload service."""

from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Any

from src.services.cloud_upload import upload_to_s3, upload_file


def _make_fake_boto3(client_obj: Any) -> types.ModuleType:
    module = types.ModuleType("boto3")

    def _client(*_args: Any, **_kwargs: Any) -> Any:
        return client_obj

    setattr(module, "client", _client)
    return module


def test_upload_to_s3_missing_file_returns_false(tmp_path: Path) -> None:
    fake_boto3 = _make_fake_boto3(client_obj=None)
    original = sys.modules.get("boto3")
    sys.modules["boto3"] = fake_boto3
    try:
        missing = tmp_path / "missing.mp4"
        assert upload_to_s3(str(missing), "bucket") is False
    finally:
        if original is not None:
            sys.modules["boto3"] = original
        else:
            del sys.modules["boto3"]


def test_upload_to_s3_success(tmp_path: Path) -> None:
    uploaded = {}

    class _FakeClient:
        def upload_file(self, filepath: str, bucket: str, key: str) -> None:
            uploaded["filepath"] = filepath
            uploaded["bucket"] = bucket
            uploaded["key"] = key

    fake_boto3 = _make_fake_boto3(client_obj=_FakeClient())
    original = sys.modules.get("boto3")
    sys.modules["boto3"] = fake_boto3
    try:
        media = tmp_path / "media.mp4"
        media.write_text("x", encoding="utf-8")
        assert upload_to_s3(str(media), "bucket-a") is True
        assert uploaded["bucket"] == "bucket-a"
        assert uploaded["key"] == "media.mp4"
    finally:
        if original is not None:
            sys.modules["boto3"] = original
        else:
            del sys.modules["boto3"]


def test_upload_file_unknown_provider_returns_false(tmp_path: Path) -> None:
    media = tmp_path / "media.mp4"
    media.write_text("x", encoding="utf-8")
    assert upload_file(str(media), "unknown") is False
