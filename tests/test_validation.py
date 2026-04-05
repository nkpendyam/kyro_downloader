"""Tests for validation utilities."""
from src.utils.validation import validate_url, validate_output_path, validate_integer, sanitize_filename, validate_batch_file

class TestValidateUrl:
    def test_valid_https_url(self):
        assert validate_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True

    def test_valid_http_url(self):
        assert validate_url("http://example.com/video") is True

    def test_valid_url_with_port(self):
        assert validate_url("https://example.com:8080/video") is True

    def test_valid_url_with_ip(self):
        assert validate_url("http://192.168.1.1/video") is True

    def test_invalid_url_no_scheme(self):
        assert validate_url("example.com/video") is False

    def test_invalid_empty_string(self):
        assert validate_url("") is False

    def test_invalid_none(self):
        assert validate_url(None) is False

    def test_invalid_not_string(self):
        assert validate_url(123) is False

    def test_valid_vimeo_url(self):
        assert validate_url("https://vimeo.com/123456789") is True

    def test_valid_tiktok_url(self):
        assert validate_url("https://www.tiktok.com/@user/video/123") is True


class TestValidateOutputPath:
    def test_valid_path(self, tmp_path):
        result = validate_output_path(str(tmp_path / "downloads"))
        assert result.exists()

    def test_empty_string_defaults(self):
        result = validate_output_path("")
        assert result.exists()

    def test_none_defaults(self):
        result = validate_output_path(None)
        assert result.exists()


class TestValidateInteger:
    def test_valid_integer(self):
        assert validate_integer("42") == 42

    def test_valid_integer_with_min(self):
        assert validate_integer("5", min_val=0) == 5

    def test_valid_integer_with_max(self):
        assert validate_integer("5", max_val=10) == 5

    def test_below_min(self):
        assert validate_integer("-1", min_val=0) is None

    def test_above_max(self):
        assert validate_integer("100", max_val=10) is None

    def test_invalid_string(self):
        assert validate_integer("abc") is None

    def test_none_value(self):
        assert validate_integer(None) is None


class TestSanitizeFilename:
    def test_removes_invalid_chars(self):
        assert "/" not in sanitize_filename("foo/bar")
        assert "\\" not in sanitize_filename("foo\\bar")

    def test_truncates_long_names(self):
        result = sanitize_filename("a" * 300)
        assert len(result) <= 200

    def test_empty_returns_untitled(self):
        assert sanitize_filename("") == "untitled"

    def test_strips_whitespace(self):
        assert sanitize_filename("  hello  ") == "hello"


class TestValidateBatchFile:
    def test_valid_batch_file(self, tmp_path):
        batch = tmp_path / "urls.txt"
        batch.write_text("https://youtube.com/watch?v=abc\nhttps://vimeo.com/123\n# comment\n")
        urls = validate_batch_file(str(batch))
        assert len(urls) == 2

    def test_missing_file_raises(self, tmp_path):
        import pytest
        with pytest.raises(FileNotFoundError):
            validate_batch_file(str(tmp_path / "missing.txt"))

    def test_empty_file(self, tmp_path):
        batch = tmp_path / "empty.txt"
        batch.write_text("")
        urls = validate_batch_file(str(batch))
        assert urls == []

    def test_ignores_invalid_urls(self, tmp_path):
        batch = tmp_path / "mixed.txt"
        batch.write_text("https://youtube.com/watch?v=abc\nnot-a-url\n")
        urls = validate_batch_file(str(batch))
        assert len(urls) == 1
