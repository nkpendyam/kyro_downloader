"""Tests for dedup utilities."""

from src.utils.dedup import get_file_hash, check_duplicate, generate_unique_filename


class TestGetFileHash:
    def test_sha256_hash(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello")
        h = get_file_hash(str(f))
        assert h is not None
        assert len(h) == 64

    def test_different_files_different_hashes(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("hello")
        f2.write_text("world")
        assert get_file_hash(str(f1)) != get_file_hash(str(f2))

    def test_same_file_same_hash(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello")
        assert get_file_hash(str(f)) == get_file_hash(str(f))

    def test_missing_file_returns_none(self):
        assert get_file_hash("/nonexistent/file.txt") is None


class TestCheckDuplicate:
    def test_no_duplicate(self, tmp_path):
        result = check_duplicate(str(tmp_path), "nonexistent")
        assert result is None

    def test_finds_duplicate(self, tmp_path):
        f = tmp_path / "title.mp4"
        f.write_text("content")
        result = check_duplicate(str(tmp_path), "title")
        assert result is not None
        path, file_hash = result
        assert str(path).endswith("title.mp4")
        assert file_hash is not None


class TestGenerateUniqueFilename:
    def test_no_conflict(self, tmp_path):
        result = generate_unique_filename(str(tmp_path), "title")
        assert result == "title.mp4"

    def test_adds_counter_on_conflict(self, tmp_path):
        f = tmp_path / "title.mp4"
        f.write_text("content")
        result = generate_unique_filename(str(tmp_path), "title")
        assert result == "title (1).mp4"

    def test_increments_counter(self, tmp_path):
        (tmp_path / "title.mp4").write_text("a")
        (tmp_path / "title (1).mp4").write_text("b")
        result = generate_unique_filename(str(tmp_path), "title")
        assert result == "title (2).mp4"
