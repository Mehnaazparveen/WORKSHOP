import unittest
import os
import tempfile
import database
import matcher
from app import app


class TestCampusLostAndFound(unittest.TestCase):
    def setUp(self):
        # Create a unique temporary database for clean test isolation
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        database.init_db(self.db_path)

        # Configure Flask app for testing
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()

        # Monkeypatch default db path for database calls in testing
        self.original_default_db = database.DEFAULT_DB_PATH
        database.DEFAULT_DB_PATH = self.db_path

    def tearDown(self):
        database.DEFAULT_DB_PATH = self.original_default_db
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    # ------------------ Database Tests ------------------
    def test_database_crud_and_status(self):
        item_id = database.create_item(
            item_type="lost",
            title="Silver MacBook Pro",
            category="Electronics",
            color="Silver",
            description="14-inch M2 MacBook with GitHub sticker",
            date_reported="2025-05-12",
            location="Library 2nd floor",
            contact_info="student@campus.edu",
            db_path=self.db_path,
        )
        self.assertIsNotNone(item_id)

        item = database.get_item_by_id(item_id, db_path=self.db_path)
        self.assertEqual(item["title"], "Silver MacBook Pro")
        self.assertEqual(item["status"], "Active")

        # Update status to Returned
        success = database.update_item_status(item_id, "Returned", db_path=self.db_path)
        self.assertTrue(success)

        updated_item = database.get_item_by_id(item_id, db_path=self.db_path)
        self.assertEqual(updated_item["status"], "Returned")

        # Test stats
        stats = database.get_dashboard_stats(db_path=self.db_path)
        self.assertEqual(stats["total_lost"], 1)
        self.assertEqual(stats["total_found"], 0)
        self.assertEqual(stats["total_returned"], 1)
        self.assertEqual(stats["total_active"], 0)

    # ------------------ Matcher Engine Tests ------------------
    def test_similarity_matching(self):
        lost_items = [
            {
                "id": 1,
                "title": "Black Bose Headphones",
                "category": "Electronics",
                "color": "Black",
                "description": "QuietComfort noise cancelling over-ear headphones in case",
                "location": "Science Hall 101",
            },
            {
                "id": 2,
                "title": "Red Hydro Flask",
                "category": "Personal Accessories",
                "color": "Red",
                "description": "32oz wide mouth insulated water bottle",
                "location": "Campus Recreation Center",
            },
        ]

        found_items = [
            {
                "id": 101,
                "title": "Bose Noise Cancelling Headphones",
                "category": "Electronics",
                "color": "Black",
                "description": "Black Bose over ear headphones found on lecture desk",
                "location": "Science Building Room 101",
            },
            {
                "id": 102,
                "title": "Green Notebook",
                "category": "Books & Stationery",
                "color": "Green",
                "description": "Spiral calculus notebook with handwritten notes",
                "location": "Dining Hall",
            },
        ]

        matches = matcher.compute_matches(lost_items, found_items, threshold=0.15)
        self.assertGreaterEqual(len(matches), 1)

        best_match = matches[0]
        self.assertEqual(best_match["lost_item"]["id"], 1)
        self.assertEqual(best_match["found_item"]["id"], 101)
        self.assertGreater(best_match["percentage"], 40)
        self.assertTrue(best_match["category_match"])

        # Test single item matcher helper
        single_matches = matcher.find_matches_for_item(lost_items[0], found_items, threshold=0.15)
        self.assertEqual(len(single_matches), 1)
        self.assertEqual(single_matches[0]["matched_item"]["id"], 101)

    # ------------------ Flask Web Route Tests ------------------
    def test_routes_dashboard_and_items(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Smart Campus", response.data)
        self.assertIn(b"Total Lost Items", response.data)

        # Submit a lost item report via POST
        post_lost = self.client.post(
            "/report/lost",
            data={
                "title": "Calculus Textbook 9th Edition",
                "category": "Books & Stationery",
                "color": "Blue",
                "description": "Stewart Calculus hardcover with sticky notes",
                "date_reported": "2025-05-15",
                "location": "Math Building Room 204",
                "contact_info": "math_major@campus.edu",
            },
            follow_redirects=True,
        )
        self.assertEqual(post_lost.status_code, 200)
        self.assertIn(b"Calculus Textbook 9th Edition", post_lost.data)

        # Submit a found item report via POST
        post_found = self.client.post(
            "/report/found",
            data={
                "title": "Stewart Calculus Hardcover Book",
                "category": "Books & Stationery",
                "color": "Blue",
                "description": "Blue hardcover textbook found on bench near Math Hall",
                "date_reported": "2025-05-15",
                "location": "Math Building Hallway",
                "contact_info": "security@campus.edu",
            },
            follow_redirects=True,
        )
        self.assertEqual(post_found.status_code, 200)
        self.assertIn(b"Stewart Calculus Hardcover Book", post_found.data)

        # Browse items catalog
        cat_resp = self.client.get("/items")
        self.assertEqual(cat_resp.status_code, 200)
        self.assertIn(b"Calculus Textbook 9th Edition", cat_resp.data)
        self.assertIn(b"Stewart Calculus Hardcover Book", cat_resp.data)

        # Check Smart Matcher page
        matches_resp = self.client.get("/matches")
        self.assertEqual(matches_resp.status_code, 200)
        self.assertIn(b"Calculus Textbook", matches_resp.data)

        # Test Status Update endpoint to Returned
        # Fetch lost item id
        items = database.get_items(item_type="lost", db_path=self.db_path)
        self.assertGreaterEqual(len(items), 1)
        lost_id = items[0]["id"]

        status_update_resp = self.client.post(
            f"/item/{lost_id}/status",
            data={"status": "Returned"},
            follow_redirects=True,
        )
        self.assertEqual(status_update_resp.status_code, 200)
        updated_item = database.get_item_by_id(lost_id, db_path=self.db_path)
        self.assertEqual(updated_item["status"], "Returned")

        # Test API endpoint
        api_resp = self.client.get("/api/matches")
        self.assertEqual(api_resp.status_code, 200)
        data = api_resp.get_json()
        self.assertEqual(data["status"], "success")


if __name__ == "__main__":
    unittest.main()
