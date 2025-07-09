import unittest
import os
import db

class TestDB(unittest.TestCase):

    def setUp(self):
        # Use a test database file
        self.test_db_path = "test_api_key_store.db"
        db.DB_PATH = self.test_db_path
        db.initialize_db()

    def tearDown(self):
        # Remove test database file
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_save_and_get_api_key(self):
        service = "test_service"
        api_key = "test_key_123"
        db.save_api_key(service, api_key)
        retrieved_key = db.get_api_key(service)
        self.assertEqual(api_key, retrieved_key)

    def test_get_api_key_nonexistent(self):
        self.assertIsNone(db.get_api_key("nonexistent_service"))

if __name__ == "__main__":
    unittest.main()
