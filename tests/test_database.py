import os
import tempfile
import unittest
from datetime import date
from pathlib import Path

import database


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "vault.sqlite3"
        self.previous_path = os.environ.get("MEMORY_VAULT_DB")
        os.environ["MEMORY_VAULT_DB"] = str(self.database_path)
        database.initialize_database()

    def tearDown(self):
        if self.previous_path is None:
            os.environ.pop("MEMORY_VAULT_DB", None)
        else:
            os.environ["MEMORY_VAULT_DB"] = self.previous_path
        self.temp_dir.cleanup()

    def test_seed_search_upload_favorite_and_capsule(self):
        self.assertEqual(len(database.list_memories()), 5)
        self.assertTrue(database.list_memories(search="sunset"))
        memory_id = database.create_memory(
            title="Test afternoon",
            memory_date=date(2026, 10, 7),
            location="Test Harbor",
            description="A lovely test moment.",
            category="Special Moments",
            tags=["test", "friends"],
            people=["Maya"],
            favorite=True,
            photos=[{"data": b"image-bytes", "caption": "Test photo"}],
        )
        saved = database.get_memory(memory_id)
        self.assertIsNotNone(saved)
        self.assertEqual(saved["photos"][0]["photo_data"], b"image-bytes")
        self.assertTrue(saved["favorite"])

        capsule_id = database.create_capsule(
            title="Open later",
            message="Hello, future me.",
            unlock_date=date(2030, 10, 7),
            memory_id=memory_id,
        )
        capsule = next(item for item in database.list_capsules() if item["id"] == capsule_id)
        self.assertEqual(capsule["cover_data"], b"image-bytes")

    def test_clear_stays_empty_and_removes_story(self):
        database.set_setting("generated_story", '{"title":"Test"}')
        database.clear_all_data()
        database.initialize_database()
        self.assertEqual(database.list_memories(), [])
        self.assertIsNone(database.get_setting("generated_story"))


if __name__ == "__main__":
    unittest.main()