"""Local story, search, and memory-label helpers."""

from __future__ import annotations

import re
from datetime import date
from typing import Any


SYNONYMS = {
    "sunset": {"sunset", "sunrise", "golden", "evening", "sky", "dusk", "apricot"},
    "friend": {"friend", "friends", "bestie", "group", "crew", "college", "selfie"},
    "friends": {"friend", "friends", "bestie", "group", "crew", "college", "selfie"},
    "beach": {"beach", "sea", "water", "shore", "ocean", "goa"},
    "family": {"family", "home", "parents", "sunday"},
    "college": {"college", "campus", "class", "friends"},
    "happy": {"happy", "birthday", "celebration", "laugh", "smile", "friends", "family"},
    "happiest": {"happy", "birthday", "celebration", "laugh", "smile", "friends", "family"},
    "food": {"food", "lunch", "dinner", "restaurant", "meal", "coffee", "cake"},
    "travel": {"travel", "trip", "goa", "beach", "vacation", "holiday"},
}
STOP_WORDS = {
    "show", "find", "with", "that", "this", "photos", "photo", "memories",
    "memory", "me", "my", "the", "and", "for", "from", "what", "did", "i",
}


def suggest_title(filenames: list[str], category: str, location: str) -> str:
    stems = [re.sub(r"\.[^.]+$", "", name).replace("_", " ").replace("-", " ") for name in filenames]
    useful = [re.sub(r"\b(IMG|DSC|PXL|PHOTO)\s*\d+\b", "", stem, flags=re.I).strip() for stem in stems]
    useful = [name for name in useful if name and not re.fullmatch(r"\d+", name)]
    if useful:
        label = re.sub(r"\s+", " ", useful[0]).strip().title()
        return label if len(label) <= 42 else label[:39].rstrip() + "..."
    if location:
        return f"A little time in {location}"
    return f"{category} in {date.today():%B}"


def parse_list(value: str) -> list[str]:
    return list(dict.fromkeys(item.strip() for item in re.split(r"[,\n]", value) if item.strip()))[:12]


def create_story(memories: list[dict[str, Any]]) -> dict[str, Any]:
    if not memories:
        return {"title": "A story still taking shape", "paragraphs": ["Add a memory to begin your story."]}
    ordered = sorted(memories, key=lambda item: item["date"])
    first, last = ordered[0], ordered[-1]
    places = list(dict.fromkeys(item["location"] for item in ordered if item["location"]))
    people = list(dict.fromkeys(person for item in ordered for person in item["people"]))[:5]
    moments = [
        item["description"].strip().rstrip(".!?")
        for item in ordered
        if item["description"].strip()
    ]
    paragraphs = [
        f"It began with {first['title'].lower()}, back in {date.fromisoformat(first['date']).strftime('%B %Y')}. Somewhere along the way, {len(ordered)} little chapters started to feel like one bigger story.",
        (". ".join(moments[:3]) + ". Each one holds onto a detail an ordinary camera roll might have let slip away.")
        if moments
        else "There are places you return to, people who make an ordinary day brighter, and small details worth finding again.",
        f"Across {', '.join(places[:3]) if places else 'the places that feel like yours'}{', with ' + ', '.join(people) if people else ''}, the days have made room for laughter, change, and the quiet things that matter. {last['title']} is only the latest page; the best part is that the story is still yours to keep.",
    ]
    return {"title": "The little things that became everything", "paragraphs": paragraphs}


def search_score(memory: dict[str, Any], query: str) -> int:
    normalized = query.lower().strip()
    terms = [word for word in re.findall(r"[\w'-]+", normalized) if len(word) > 2 and word not in STOP_WORDS]
    expanded: set[str] = set()
    for term in terms:
        expanded.update(SYNONYMS.get(term, {term}))
    if not expanded:
        expanded.add(normalized)
    date_label = date.fromisoformat(memory["date"]).strftime("%B %Y").lower()
    main_text = " ".join(
        [memory["title"], memory["location"], memory["description"], memory["category"], date_label]
        + memory["tags"]
        + memory["people"]
    ).lower()
    photo_text = " ".join(
        f"{photo.get('caption', '')} {photo.get('captured_at', '')}"
        for photo in memory.get("photos", [])
    ).lower()
    return sum(3 if term in photo_text else 2 if term in main_text else 0 for term in expanded)