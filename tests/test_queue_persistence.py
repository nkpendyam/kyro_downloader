"""Queue persistence restart tests."""

from __future__ import annotations


from src.core.download_manager import DownloadManager
from src.core.queue import DownloadQueue


class TestQueuePersistence:
    def test_export_and_import_state_restores_items(self, tmp_path):
        q1 = DownloadQueue()
        q1.add(url="https://example.com/one")
        q1.add(url="https://example.com/two")

        exported = q1.export_state()
        assert exported["version"] == 1
        assert len(exported["items"]) == 2

        q2 = DownloadQueue()
        restored = q2.import_state(exported)
        assert restored == 2
        assert q2.size == 2

    def test_completed_items_not_restored(self, tmp_path):
        q1 = DownloadQueue()
        q1.add(url="https://example.com/pending")
        active = q1.add(url="https://example.com/active")
        q1.get_next()
        q1.complete(active.task_id)

        exported = q1.export_state()
        urls = {item["url"] for item in exported["items"]}
        assert "https://example.com/pending" in urls
        assert "https://example.com/active" not in urls

    def test_cancelled_items_not_restored(self, tmp_path):
        q1 = DownloadQueue()
        item = q1.add(url="https://example.com/cancelled")
        q1.cancel(item.task_id)

        exported = q1.export_state()
        assert len(exported["items"]) == 0

    def test_paused_items_restored_with_paused_status(self, tmp_path):
        q1 = DownloadQueue()
        item = q1.add(url="https://example.com/paused")
        q1.pause(item.task_id)

        exported = q1.export_state()
        assert len(exported["items"]) == 1
        assert exported["items"][0]["status"] == "paused"

        q2 = DownloadQueue()
        q2.import_state(exported)
        restored = q2.get_item(item.task_id)
        assert restored is not None
        assert restored.status.value == "paused"

    def test_corrupted_state_file_handled_gracefully(self, tmp_path):
        state_path = tmp_path / "queue.json"
        state_path.write_text("{invalid json content", encoding="utf-8")

        dm = DownloadManager(config={"queue_state_path": str(state_path), "output_path": str(tmp_path)})
        assert dm.queue.size == 0

    def test_manager_save_and_restore_across_instances(self, tmp_path):
        state_path = tmp_path / "queue.json"
        output_dir = tmp_path / "downloads"
        output_dir.mkdir()

        dm1 = DownloadManager(config={"queue_state_path": str(state_path), "output_path": str(output_dir)})
        dm1.queue.add(url="https://example.com/video1")
        dm1.queue.add(url="https://example.com/video2")
        dm1._save_queue_state()

        assert state_path.exists()

        dm2 = DownloadManager(config={"queue_state_path": str(state_path), "output_path": str(output_dir)})
        assert dm2.queue.size == 2
