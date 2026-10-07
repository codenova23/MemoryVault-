import unittest
from datetime import date

from memory_vault.services import create_story, parse_list, search_score, suggest_title


def memory(**overrides):
    result = {
        "title": "The long way home",
        "date": "2024-10-07",
        "location": "Marine Drive, Mumbai",
        "description": "We stopped for five minutes. The sky had other plans.",
        "category": "Nature",
        "tags": ["Nature", "Sunset", "Friends", "Evening"],
        "people": ["Maya"],
        "photos": [{"caption": "Five more minutes", "captured_at": "5:42 PM"}],
    }
    result.update(overrides)
    return result


class MemoryServiceTests(unittest.TestCase):
    def test_search_expands_natural_language_and_dates(self):
        sunset = memory()
        birthday = memory(
            title="A birthday in full color",
            date="2026-07-20",
            location="Mumbai, India",
            description="A tiny cake and lots of happy tears.",
            category="Celebrations",
            tags=["Birthday", "Friends"],
            people=["Nina"],
            photos=[{"caption": "Make a wish", "captured_at": "8:30 PM"}],
        )
        self.assertGreater(search_score(sunset, "sunset photos with my friends"), 0)
        self.assertGreater(search_score(memory(date="2026-08-14"), "August"), 0)
        self.assertEqual(search_score(birthday, "sunset photos"), 0)

    def test_generated_story_connects_memory_details(self):
        story = create_story([memory(), memory(title="Sunday at home", date="2026-06-07")])
        joined = " ".join(story["paragraphs"])
        self.assertEqual(story["title"], "The little things that became everything")
        self.assertIn("2 little chapters", joined)
        self.assertIn("Maya", joined)

    def test_title_and_tag_helpers_handle_camera_filenames(self):
        self.assertEqual(suggest_title(["PXL_12345.jpg"], "Travel", "Goa"), "A little time in Goa")
        self.assertEqual(suggest_title([], "Family", ""), f"Family in {date.today():%B}")
        self.assertEqual(parse_list("friends, beach, friends"), ["friends", "beach"])


if __name__ == "__main__":
    unittest.main()