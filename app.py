"""Memory Vault: local-first Streamlit memory organizer."""

from __future__ import annotations

import hashlib
import html
import hmac
import io
import json
import os
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Any

import streamlit as st
from PIL import Image, ImageOps

import database


st.set_page_config(
    page_title="Memory Vault | Preserve Moments. Relive Stories.",
    page_icon="🗝️",
    layout="wide",
    initial_sidebar_state="expanded",
)

CATEGORIES = [
    "Friends",
    "Family",
    "College",
    "Travel",
    "Celebrations",
    "Nature",
    "Food",
    "Special Moments",
]
CATEGORY_ICONS = {
    "Friends": "♡",
    "Family": "⌂",
    "College": "✳",
    "Travel": "↗",
    "Celebrations": "✦",
    "Nature": "☼",
    "Food": "◌",
    "Special Moments": "✧",
}
SYNONYMS = {
    "sunset": {"sunset", "sunrise", "golden", "evening", "sky", "dusk", "apricot"},
    "friend": {"friend", "friends", "bestie", "group", "crew", "college", "selfie"},
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


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&family=Playfair+Display:ital,wght@0,500;0,600;1,500&display=swap');
        :root { --ink:#261f38; --purple:#7656cf; --muted:#888396; --line:#ece9f1; --paper:#f7f6fa; }
        html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
        .stApp { color:var(--ink); background:var(--paper); }
        [data-testid="stHeader"] { background:rgba(247,246,250,.88); }
        [data-testid="stSidebar"] { background:#221a36; border-right:1px solid #ffffff12; }
        [data-testid="stSidebar"] * { color:#f0edf6; }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#beb6cd; }
        [data-testid="stSidebar"] [data-testid="stRadio"] label { border-radius:7px; }
        [data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background:#ffffff10; }
        [data-testid="stSidebar"] [data-testid="stMetricValue"] { color:#fff; }
        .block-container { max-width:1380px; padding:1.8rem clamp(1rem,4vw,4rem) 1rem; }
        h1,h2,h3 { color:#2d263d; font-family:'Manrope',sans-serif; letter-spacing:-.035em; }
        h1 { font-size:2.2rem!important; font-weight:700!important; }
        h2 { font-size:1.35rem!important; font-weight:700!important; }
        h3 { font-size:1.02rem!important; font-weight:700!important; }
        p,li { color:#777181; }
        [data-testid="stMetric"] { min-height:92px; padding:15px 17px; border:1px solid #eae7ef; border-radius:10px; background:#fff; box-shadow:0 4px 15px #281c4507; }
        [data-testid="stMetricLabel"] { color:#918a9d; font-size:.76rem; }
        [data-testid="stMetricValue"] { color:#362d48; font-family:'Manrope',sans-serif; font-size:1.65rem; font-weight:700; }
        [data-testid="stVerticalBlockBorderWrapper"] { border-color:#eae7ef!important; border-radius:10px!important; background:#fff; }
        .stButton > button, .stFormSubmitButton > button { min-height:2.45rem; border:1px solid #ded5ef; border-radius:7px; color:#6d5a9c; background:#fff; font-size:.83rem; font-weight:700; transition:all .18s ease; }
        .stButton > button:hover, .stFormSubmitButton > button:hover { border-color:#bba9e1; color:#5e43a8; background:#f7f4fd; transform:translateY(-1px); }
        .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] { border-color:#7656cf; color:white; background:#7656cf; box-shadow:0 5px 15px #6243a72b; }
        .stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover { border-color:#6044b3; background:#6044b3; }
        [data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-testid="stDateInput"] input,[data-testid="stSelectbox"] div[data-baseweb="select"] { border-radius:7px; }
        [data-testid="stFileUploader"] section { border-color:#d8cfea; border-radius:8px; background:#fcfbfe; }
        [data-testid="stExpander"] { border-color:#eae7ef; border-radius:8px; background:#fff; }
        .mv-brand { display:flex; align-items:center; gap:10px; margin:4px 0 22px; color:#fff; font:800 15px Manrope,sans-serif; letter-spacing:.02em; }
        .mv-brand-mark { display:grid; width:36px; height:36px; place-items:center; border:1px solid #927bd1; border-radius:11px; color:#dbcfff; background:#6550a2; font-size:18px; }
        .mv-brand small { display:block; margin-top:3px; color:#aaa1c1; font:700 7px 'DM Sans',sans-serif; letter-spacing:1.1px; }
        .mv-eyebrow { color:#8875b6; font-size:9px; font-weight:700; letter-spacing:1.4px; text-transform:uppercase; }
        .mv-hero { position:relative; overflow:hidden; min-height:248px; padding:29px 32px; border:1px solid #e5dff2; border-radius:12px; background:linear-gradient(112deg,#eee9f9,#f1ebf7 57%,#eae7f5); }
        .mv-hero:after { position:absolute; right:7%; bottom:-65px; color:#9178c52e; font:220px 'Playfair Display',serif; content:'“'; }
        .mv-hero h1 { margin:.55rem 0 .65rem; font-size:clamp(2rem,4vw,3rem)!important; line-height:1.1; }
        .mv-hero h1 em { color:#7858c8; font:italic 500 1em 'Playfair Display',serif; }
        .mv-hero p { max-width:485px; font-size:.9rem; line-height:1.7; }
        .mv-hero-note { margin-top:13px; color:#8c8496; font-size:.72rem; }
        .mv-section-head { display:flex; align-items:end; justify-content:space-between; margin:1.7rem 0 .7rem; }
        .mv-section-head h2 { margin:.2rem 0 0; }
        .mv-card { overflow:hidden; margin-bottom:.8rem; border:1px solid #eae7ef; border-radius:9px; background:#fff; box-shadow:0 4px 15px #281c4507; transition:transform .2s,box-shadow .2s; }
        .mv-card:hover { transform:translateY(-3px); box-shadow:0 16px 45px #2b204314; }
        .mv-card img { width:100%; height:170px; object-fit:cover; }
        .mv-card-body { padding:12px 13px 13px; }
        .mv-card-title { margin:0 0 5px; color:#393144; font:700 14px Manrope,sans-serif; }
        .mv-card-meta { color:#938d9c; font-size:10px; }
        .mv-card-desc { min-height:31px; margin:8px 0 10px; color:#777181; font-size:11px; line-height:1.55; }
        .mv-tags { display:flex; flex-wrap:wrap; gap:5px; }
        .mv-tag { padding:4px 8px; border-radius:20px; color:#6f5d9a; background:#f0ecf8; font-size:9px; }
        .mv-tag:nth-child(even) { color:#94688b; background:#f6edf5; }
        .mv-quote { padding:18px 20px; border:1px solid #e7dff2; border-radius:9px; background:linear-gradient(120deg,#f1edf9,#f7f1f8); color:#5b506d; font:italic 14px/1.75 'Playfair Display',serif; }
        .mv-privacy { padding:18px 20px; border:1px solid #e5e0ee; border-radius:9px; background:#f1eef8; }
        .mv-timeline-year { margin:.5rem 0; padding:4px 0; color:#7258b5; font:700 1.1rem Manrope,sans-serif; }
        .mv-detail-image img { border-radius:9px; }
        .mv-footer { display:flex; justify-content:space-between; gap:12px; margin-top:25px; padding:16px 0 8px; border-top:1px solid #ece9f1; color:#aaa5b2; font-size:9px; }
        .stAlert { border-radius:8px; }
        @media(max-width:700px) { .block-container{padding:1rem .85rem .7rem}.mv-hero{padding:23px 19px}.mv-hero h1{font-size:2rem!important}.mv-card img{height:145px}.mv-footer{flex-direction:column;gap:5px} }
        </style>
        """,
        unsafe_allow_html=True,
    )


def configured_password() -> str:
    try:
        password = st.secrets.get("APP_PASSWORD", "")
    except Exception:
        password = ""
    return str(password or os.environ.get("APP_PASSWORD", ""))


def require_access() -> bool:
    password = configured_password()
    if not password:
        return True
    if st.session_state.get("authenticated"):
        return True
    st.markdown('<div class="mv-brand"><span class="mv-brand-mark">✦</span><span>MEMORY VAULT<small>YOUR LIFE, LOVINGLY KEPT</small></span></div>', unsafe_allow_html=True)
    st.markdown('<div class="mv-eyebrow">A PRIVATE MEMORY SPACE</div>', unsafe_allow_html=True)
    st.title("Welcome back to your vault.")
    entered = st.text_input("Vault password", type="password")
    if st.button("Unlock Memory Vault", type="primary"):
        if hmac.compare_digest(entered, password):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("That password doesn't match. Try again.")
    st.caption("This single-owner password gate is optional. Configure APP_PASSWORD in Streamlit secrets before sharing a deployed app.")
    return False


def image_bytes(uploaded_file: Any) -> bytes:
    image = Image.open(uploaded_file)
    image = ImageOps.exif_transpose(image).convert("RGB")
    image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=82, optimize=True)
    return output.getvalue()


def image_source(photo: dict[str, Any]) -> bytes | str | None:
    return photo.get("photo_data") or photo.get("photo_url") or None


def image_for_memory(memory: dict[str, Any]) -> bytes | str | None:
    photos = memory.get("photos") or []
    return image_source(photos[0]) if photos else None


def suggest_title(filenames: list[str], category: str, location: str) -> str:
    stems = [re.sub(r"\.[^.]+$", "", name).replace("_", " ").replace("-", " ") for name in filenames]
    useful = [re.sub(r"\b(IMG|DSC|PXL|PHOTO)\s*\d+\b", "", stem, flags=re.I).strip() for stem in stems]
    useful = [name for name in useful if name and not re.fullmatch(r"\d+", name)]
    if useful:
        label = re.sub(r"\s+", " ", useful[0]).strip().title()
        if len(label) > 42:
            label = label[:39].rstrip() + "..."
        return label
    if location:
        return f"A little time in {location}"
    month = date.today().strftime("%B")
    return f"{category} in {month}"


def parse_list(value: str) -> list[str]:
    return list(dict.fromkeys(item.strip() for item in re.split(r"[,\n]", value) if item.strip()))[:12]


def photo_time(index: int) -> str:
    moment = datetime.now().replace(hour=10, minute=30, second=0, microsecond=0) + timedelta(minutes=74 * index)
    return moment.strftime("%-I:%M %p")


def create_story(memories: list[dict[str, Any]]) -> dict[str, Any]:
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
    score = 0
    for term in expanded:
        if term in photo_text:
            score += 3
        elif term in main_text:
            score += 2
    return score


def memory_card(memory: dict[str, Any], key_suffix: str = "") -> None:
    photo = image_for_memory(memory)
    with st.container(border=True):
        if photo:
            st.image(photo, width="stretch")
        st.markdown(f'<div class="mv-card-title">{html.escape(memory["title"])}</div>', unsafe_allow_html=True)
        date_label = date.fromisoformat(memory["date"]).strftime("%b %-d, %Y")
        location = f" · {html.escape(memory['location'])}" if memory["location"] else ""
        st.markdown(
            f'<div class="mv-card-meta">{date_label}{location} · {memory["category"]}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(f'<div class="mv-card-desc">{html.escape(memory["description"])}</div>', unsafe_allow_html=True)
        tags = "".join(f'<span class="mv-tag">{html.escape(tag)}</span>' for tag in memory["tags"][:4])
        st.markdown(f'<div class="mv-tags">{tags}</div>', unsafe_allow_html=True)
        first, second = st.columns([1.25, 1], gap="small")
        if first.button("Open memory", key=f"open-{memory['id']}-{key_suffix}", width="stretch"):
            st.session_state.selected_memory_id = memory["id"]
            st.rerun()
        favorite_label = "♥ Saved" if memory["favorite"] else "♡ Favorite"
        if second.button(favorite_label, key=f"favorite-{memory['id']}-{key_suffix}", width="stretch"):
            database.set_favorite(memory["id"], not memory["favorite"])
            st.rerun()


def section_heading(eyebrow: str, title: str, subtitle: str | None = None) -> None:
    st.markdown(f'<div class="mv-eyebrow">{html.escape(eyebrow)}</div>', unsafe_allow_html=True)
    st.title(title)
    if subtitle:
        st.caption(subtitle)


def render_dashboard() -> None:
    memories = database.list_memories()
    favorites = [memory for memory in memories if memory["favorite"]]
    capsules = database.list_capsules()
    st.markdown(
        """<section class="mv-hero"><div class="mv-eyebrow">YOUR LIFE, LOVINGLY KEPT</div>
        <h1>Preserve Moments.<br><em>Relive Stories.</em></h1>
        <p>Your best memories deserve more than a camera roll. Give every moment a place, a little context, and a way back.</p>
        <div class="mv-hero-note">Private by nature · A little story behind every photo</div></section>""",
        unsafe_allow_html=True,
    )
    st.write("")
    first, second, third = st.columns(3)
    first.metric("Memories saved", len(memories), help="All the little chapters in your vault")
    second.metric("Favorite moments", len(favorites), help="Memories you have marked as favorites")
    third.metric("Future capsules", len(capsules), help="Notes waiting for their unlock date")

    st.markdown(
        '<div class="mv-section-head"><div><div class="mv-eyebrow">A FEW RECENT FAVORITES</div><h2>Moments, lately.</h2></div></div>',
        unsafe_allow_html=True,
    )
    recent = memories[:3]
    if not recent:
        st.info("Your story starts here. Add a photo and give your first moment a home.")
        if st.button("Create a memory", type="primary"):
            st.session_state.view = "Add memory"
            st.rerun()
    else:
        columns = st.columns(min(3, len(recent)), gap="medium")
        for index, memory in enumerate(recent):
            with columns[index % len(columns)]:
                memory_card(memory, "home")

    if favorites:
        st.markdown(
            '<div class="mv-section-head"><div><div class="mv-eyebrow">KEPT A LITTLE CLOSER</div><h2>Your favorites.</h2></div></div>',
            unsafe_allow_html=True,
        )
        columns = st.columns(min(3, len(favorites)), gap="medium")
        for index, memory in enumerate(favorites[:3]):
            with columns[index % len(columns)]:
                memory_card(memory, "favorite")

    today = date.today()
    on_this_day = next(
        (
            memory for memory in memories
            if date.fromisoformat(memory["date"]).month == today.month
            and date.fromisoformat(memory["date"]).day == today.day
            and date.fromisoformat(memory["date"]).year < today.year
        ),
        None,
    )
    st.markdown('<div class="mv-section-head"><div><div class="mv-eyebrow">A LITTLE HELLO FROM THE PAST</div><h2>On this day.</h2></div></div>', unsafe_allow_html=True)
    if on_this_day:
        with st.container(border=True):
            columns = st.columns([1, 2], gap="large")
            with columns[0]:
                if image_for_memory(on_this_day):
                    st.image(image_for_memory(on_this_day), width="stretch")
            with columns[1]:
                st.subheader(on_this_day["title"])
                st.caption(f"{date.fromisoformat(on_this_day['date']).strftime('%B %-d, %Y')} · {on_this_day['location']}")
                st.write(on_this_day["description"])
                if st.button("Open this memory", key="on-this-day-open"):
                    st.session_state.selected_memory_id = on_this_day["id"]
                    st.rerun()
    else:
        st.markdown('<div class="mv-quote">Some moments find their way back. Your on-this-day memories will appear here.</div>', unsafe_allow_html=True)

    counts = Counter(memory["category"] for memory in memories)
    st.markdown('<div class="mv-section-head"><div><div class="mv-eyebrow">LITTLE CHAPTERS</div><h2>Browse your collections.</h2></div></div>', unsafe_allow_html=True)
    category_columns = st.columns(4)
    for index, category in enumerate(CATEGORIES):
        with category_columns[index % len(category_columns)]:
            st.markdown(f"**{CATEGORY_ICONS[category]}  {category}**  \n{counts[category]} {'memory' if counts[category] == 1 else 'memories'}")


def render_add_memory() -> None:
    section_heading("ADD A LITTLE CHAPTER", "Save a memory", "A photo, a few details, and this moment has a place of its own.")
    upload_key = f"memory_uploads_{st.session_state.upload_nonce}"
    uploads = st.file_uploader(
        "Choose photos",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        max_upload_size=15,
        help="JPG and PNG images are compressed in your browser session before being saved.",
        key=upload_key,
    )
    if uploads:
        st.caption(f"{len(uploads)} photo{'s' if len(uploads) != 1 else ''} selected")
        preview_columns = st.columns(min(4, len(uploads)))
        for index, uploaded in enumerate(uploads[:8]):
            with preview_columns[index % len(preview_columns)]:
                st.image(uploaded, caption=uploaded.name, width="stretch")

    filenames = [uploaded.name for uploaded in uploads or []]
    with st.form("add_memory_form", clear_on_submit=False):
        first, second = st.columns(2)
        with first:
            title = st.text_input("Memory title", placeholder="A little Goa escape", max_chars=90)
            memory_date = st.date_input("Date", value=date.today(), max_value=date.today())
            location = st.text_input("Location", placeholder="A place worth remembering", max_chars=100)
            category = st.selectbox("Category", CATEGORIES)
        with second:
            description = st.text_area(
                "The story so far",
                placeholder="What do you want to remember about this day?",
                max_chars=600,
                height=130,
            )
            people_text = st.text_input("People", placeholder="Maya, Dev, Aanya")
            tags_text = st.text_input("Tags", placeholder="beach, summer, sunset")
            favorite = st.checkbox("Keep this one close — mark as a favorite")
        submitted = st.form_submit_button("Save memory", type="primary", width="stretch")

    if submitted:
        if not uploads:
            st.error("Add at least one photo to create a memory.")
            return
        if any(uploaded.size > 15 * 1024 * 1024 for uploaded in uploads):
            st.error("Each photo must be smaller than 15 MB.")
            return
        if not description.strip():
            st.error("Add a short description so this moment is easy to remember.")
            return
        final_title = title.strip() or suggest_title(filenames, category, location.strip())
        with st.spinner("Gathering the little details…"):
            try:
                photos = [
                    {"data": image_bytes(uploaded), "caption": uploaded.name, "time": photo_time(index)}
                    for index, uploaded in enumerate(uploads)
                ]
                memory_id = database.create_memory(
                    title=final_title,
                    memory_date=memory_date,
                    location=location.strip(),
                    description=description.strip(),
                    category=category,
                    tags=parse_list(tags_text) or [category],
                    people=parse_list(people_text),
                    favorite=favorite,
                    photos=photos,
                )
            except Exception as error:
                st.error(f"We couldn't save those photos. Try a smaller JPG or PNG. Details: {error}")
                return
        st.session_state.upload_nonce += 1
        st.session_state.selected_memory_id = memory_id
        st.session_state.view = "Timeline"
        st.success(f"“{final_title}” is safely tucked away.")
        st.rerun()


def render_timeline() -> None:
    if st.session_state.get("selected_memory_id"):
        render_memory_detail(st.session_state.selected_memory_id)
        return
    section_heading("A LIFE, IN LITTLE CHAPTERS", "Your story, over time", "Search, filter, and find your way back to a moment.")
    query_col, category_col, sort_col = st.columns([2, 1, 1])
    with query_col:
        query = st.text_input("Search memories", placeholder="Try a sunset with friends…", key="timeline_search")
    with category_col:
        category = st.selectbox("Category", ["All memories", *CATEGORIES], key="timeline_category")
    with sort_col:
        sort_order = st.selectbox("Sort", ["Newest first", "Oldest first"], key="timeline_sort")

    memories = database.list_memories(category=None if category == "All memories" else category)
    if query.strip():
        memories = [memory for memory in memories if search_score(memory, query) > 0]
        memories.sort(key=lambda memory: search_score(memory, query), reverse=True)
    if sort_order == "Oldest first":
        memories.reverse()
    if not memories:
        st.info("No moments matched. Try another search or category, or add a new memory.")
        if st.button("Clear filters"):
            st.session_state.timeline_search = ""
            st.session_state.timeline_category = "All memories"
            st.rerun()
        return

    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for memory in memories:
        grouped[date.fromisoformat(memory["date"]).year].append(memory)
    for year, year_memories in grouped.items():
        st.markdown(f'<div class="mv-timeline-year">{year}</div>', unsafe_allow_html=True)
        months: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for memory in year_memories:
            months[date.fromisoformat(memory["date"]).strftime("%B")].append(memory)
        for month, month_memories in months.items():
            st.markdown(f"#### {month}")
            for memory in month_memories:
                render_timeline_card(memory)


def render_timeline_card(memory: dict[str, Any]) -> None:
    with st.container(border=True):
        image_col, info_col, button_col = st.columns([1, 3, 1], vertical_alignment="center")
        with image_col:
            if image_for_memory(memory):
                st.image(image_for_memory(memory), width="stretch")
        with info_col:
            st.markdown(f"**{memory['title']}**")
            location = f" · {memory['location']}" if memory["location"] else ""
            st.caption(f"{date.fromisoformat(memory['date']).strftime('%b %-d, %Y')}{location} · {memory['category']}")
            st.write(memory["description"])
        with button_col:
            if st.button("Open", key=f"timeline-open-{memory['id']}", width="stretch"):
                st.session_state.selected_memory_id = memory["id"]
                st.rerun()


def render_memory_detail(memory_id: str) -> None:
    memory = database.get_memory(memory_id)
    if not memory:
        st.session_state.selected_memory_id = None
        st.warning("That memory is no longer in your vault.")
        return
    if st.button("← Back to timeline"):
        st.session_state.selected_memory_id = None
        st.rerun()
    st.markdown(f'<div class="mv-eyebrow">A LITTLE CHAPTER · {html.escape(memory["category"].upper())}</div>', unsafe_allow_html=True)
    st.title(memory["title"])
    meta = date.fromisoformat(memory["date"]).strftime("%B %-d, %Y")
    if memory["location"]:
        meta += f" · {memory['location']}"
    st.caption(meta)
    if memory["photos"]:
        main_image = image_source(memory["photos"][0])
        if main_image:
            st.image(main_image, width="stretch")
        if len(memory["photos"]) > 1:
            gallery = st.columns(min(4, len(memory["photos"]) - 1))
            for index, photo in enumerate(memory["photos"][1:]):
                with gallery[index % len(gallery)]:
                    if image_source(photo):
                        st.image(image_source(photo), caption=photo["caption"], width="stretch")
    st.markdown('<div class="mv-section-head"><div><div class="mv-eyebrow">THE STORY SO FAR</div><h2>A moment, remembered.</h2></div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="mv-quote">{html.escape(memory["description"])}</div>', unsafe_allow_html=True)
    st.write("")
    if memory["people"]:
        st.markdown("**With:** " + ", ".join(memory["people"]))
    st.markdown("**Tags:** " + " · ".join(memory["tags"]))
    st.markdown('<div class="mv-section-head"><div><div class="mv-eyebrow">IN THE ORDER IT HAPPENED</div><h2>A day in little moments.</h2></div></div>', unsafe_allow_html=True)
    for photo in memory["photos"]:
        captured = photo["captured_at"] or "A moment saved"
        caption = photo["caption"] or memory["title"]
        st.markdown(f"**{captured}**　{caption}")

    favorite_col, capsule_col, delete_col = st.columns(3)
    if favorite_col.button("♥ Remove favorite" if memory["favorite"] else "♡ Add favorite", width="stretch"):
        database.set_favorite(memory_id, not memory["favorite"])
        st.rerun()
    if capsule_col.button("🔒 Save as capsule", width="stretch"):
        st.session_state.capsule_memory_id = memory_id
        st.session_state.view = "Memory capsules"
        st.rerun()
    if delete_col.button("Delete memory", width="stretch"):
        st.session_state.confirm_delete_memory = memory_id
    if st.session_state.get("confirm_delete_memory") == memory_id:
        st.warning("Delete this memory and its photos? A capsule keeps its own cover image.")
        confirm_col, cancel_col = st.columns(2)
        if confirm_col.button("Yes, delete memory", type="primary", key="confirm-delete-memory"):
            database.delete_memory(memory_id)
            st.session_state.selected_memory_id = None
            st.session_state.confirm_delete_memory = None
            st.success("Memory deleted.")
            st.rerun()
        if cancel_col.button("Keep memory", key="cancel-delete-memory"):
            st.session_state.confirm_delete_memory = None
            st.rerun()


def render_story() -> None:
    memories = database.list_memories()
    section_heading("A STORY, MADE FROM YOUR MOMENTS", "Your life is already a story", "We gather the places, people, and little details you have saved, then weave them into a small story to keep.")
    if not memories:
        st.info("Add a memory first. Your story can begin with one little chapter.")
        if st.button("Create a memory", type="primary"):
            st.session_state.view = "Add memory"
            st.rerun()
        return
    if st.button("✨ Create My Story", type="primary"):
        story = create_story(memories)
        database.set_setting("generated_story", json.dumps(story))
        st.session_state.generated_story = story
    story = st.session_state.get("generated_story")
    if not story:
        saved = database.get_setting("generated_story")
        if saved:
            try:
                story = json.loads(saved)
            except json.JSONDecodeError:
                story = None
    if story:
        st.markdown('<div class="mv-section-head"><div><div class="mv-eyebrow">YOUR MEMORY VAULT STORY</div><h2>The little things that became everything</h2></div></div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f'<div class="mv-eyebrow">{html.escape(story["title"].upper())}</div>', unsafe_allow_html=True)
            for paragraph in story["paragraphs"]:
                st.markdown(f'<p style="font:16px/1.9 Playfair Display,serif;color:#62596f">{html.escape(paragraph)}</p>', unsafe_allow_html=True)
            st.caption("Written from your moments, kept just for you.")
    else:
        st.markdown('<div class="mv-quote">Your photos already hold a story. Create My Story to find the thread between them.</div>', unsafe_allow_html=True)


def render_capsules() -> None:
    st.markdown(
        """<section class="mv-hero"><div class="mv-eyebrow">🔒 A NOTE FROM NOW, FOR LATER</div>
        <h1>Leave a little <em>something.</em></h1>
        <p>Choose a future day, write yourself a note, and let a memory wait quietly until then.</p></section>""",
        unsafe_allow_html=True,
    )
    memories = database.list_memories()
    with st.expander("Create a Memory Capsule", expanded=bool(st.session_state.get("capsule_memory_id"))):
        with st.form("create_capsule_form"):
            title = st.text_input("Give this capsule a name", placeholder="A note for future me", max_chars=80)
            message = st.text_area("Your note", placeholder="What do you hope you’ll remember?", max_chars=500)
            unlock_date = st.date_input("Open this memory on", value=date.today() + timedelta(days=365), min_value=date.today() + timedelta(days=1))
            options = {"No attached memory": None}
            options.update({memory["title"]: memory["id"] for memory in memories})
            selected_label = st.selectbox("Attach a memory", list(options), index=next((index for index, key in enumerate(options) if options[key] == st.session_state.get("capsule_memory_id")), 0))
            submitted = st.form_submit_button("🔒 Tuck it away", type="primary")
        if submitted:
            if not title.strip() or not message.strip():
                st.error("Add a title and a note before saving your capsule.")
            elif unlock_date <= date.today():
                st.error("Choose a date in the future.")
            else:
                database.create_capsule(
                    title=title.strip(),
                    message=message.strip(),
                    unlock_date=unlock_date,
                    memory_id=options[selected_label],
                )
                st.session_state.capsule_memory_id = None
                st.success("Your note is tucked away for another day.")
                st.rerun()

    capsules = database.list_capsules()
    st.markdown('<div class="mv-section-head"><div><div class="mv-eyebrow">SAVED FOR ANOTHER DAY</div><h2>Your little time capsules.</h2></div></div>', unsafe_allow_html=True)
    if not capsules:
        st.info("A memory waiting for your future self. Your first capsule could open on a birthday, a reunion, or an ordinary Tuesday years from now.")
        return
    for capsule in capsules:
        unlocked = date.fromisoformat(capsule["unlock_date"]) <= date.today()
        label = f"{'🔓 Ready to open' if unlocked else '🔒 Still tucked away'} · {capsule['title']} · {date.fromisoformat(capsule['unlock_date']).strftime('%B %-d, %Y')}"
        with st.expander(label):
            photo = capsule["cover_data"] or capsule["cover_url"]
            if photo:
                st.image(photo, width=360)
            st.markdown(f'<div class="mv-quote">“{html.escape(capsule["message"])}”</div>', unsafe_allow_html=True)
            if unlocked:
                st.success("The day has arrived. Your note is ready to open.")
            else:
                remaining = (date.fromisoformat(capsule["unlock_date"]) - date.today()).days
                st.caption(f"Opens in {remaining} {'day' if remaining == 1 else 'days'} · {date.fromisoformat(capsule['unlock_date']).strftime('%B %-d, %Y')}")
            if st.button("Delete capsule", key=f"delete-capsule-{capsule['id']}"):
                st.session_state.confirm_delete_capsule = capsule["id"]
            if st.session_state.get("confirm_delete_capsule") == capsule["id"]:
                left, right = st.columns(2)
                if left.button("Confirm delete", key=f"confirm-capsule-{capsule['id']}", type="primary"):
                    database.delete_capsule(capsule["id"])
                    st.session_state.confirm_delete_capsule = None
                    st.rerun()
                if right.button("Cancel", key=f"cancel-capsule-{capsule['id']}"):
                    st.session_state.confirm_delete_capsule = None
                    st.rerun()
    st.markdown('<div class="mv-privacy">Capsules and their notes stay in this app’s database. The unlock date is checked when the vault is open; there is no scheduled email or server delivery.</div>', unsafe_allow_html=True)


def render_privacy() -> None:
    section_heading("YOUR SPACE, YOUR RULES", "Your memories belong to you", "A few clear things about where your photos and stories live.")
    st.markdown(
        '<div class="mv-privacy"><h3>Private by design. Clear about its limits.</h3><p>Memory Vault stores memory records and compressed photo bytes in SQLite. If you set APP_PASSWORD, the app adds a single-owner password gate. The demo story is generated locally in Python and makes no AI API calls. Sample cover photos are loaded from Unsplash.</p></div>',
        unsafe_allow_html=True,
    )
    memories = database.list_memories()
    capsules = database.list_capsules()
    first, second, third = st.columns(3)
    first.metric("Memories", len(memories))
    second.metric("Photos", sum(len(memory["photos"]) for memory in memories))
    third.metric("Capsules", len(capsules))
    if not configured_password():
        st.warning("No APP_PASSWORD is configured. Anyone who can reach this deployment may be able to view its shared vault. Set APP_PASSWORD in Streamlit secrets before deploying private memories.")
    st.markdown("**Storage note:** local runs use `data/memory_vault.sqlite3`. Streamlit Community Cloud may reset local files when the app restarts or is redeployed. For durable production storage, connect a managed database and object store before using irreplaceable personal photos.")
    with st.expander("Sample memories and local data"):
        st.write("Remove sample memories while keeping personal uploads, restore the five examples, or clear this database.")
        remove_col, restore_col, clear_col = st.columns(3)
        if remove_col.button("Remove samples"):
            removed = database.remove_demo_memories()
            st.success(f"Removed {removed} sample memories. Your own uploads remain.")
            st.rerun()
        if restore_col.button("Restore samples"):
            database.restore_demo_memories()
            st.success("Sample memories restored.")
            st.rerun()
        if clear_col.button("Clear all data"):
            st.session_state.confirm_clear_data = True
        if st.session_state.get("confirm_clear_data"):
            st.error("This permanently deletes every memory, photo, and capsule in this database.")
            confirm_col, cancel_col = st.columns(2)
            if confirm_col.button("Yes, clear all data", type="primary"):
                database.clear_all_data()
                st.session_state.confirm_clear_data = False
                st.session_state.selected_memory_id = None
                st.success("The vault is clear.")
                st.rerun()
            if cancel_col.button("Cancel"):
                st.session_state.confirm_clear_data = False
                st.rerun()


def main() -> None:
    database.initialize_database()
    apply_styles()
    if not require_access():
        return

    st.session_state.setdefault("view", "Dashboard")
    st.session_state.setdefault("upload_nonce", 0)
    st.session_state.setdefault("selected_memory_id", None)
    with st.sidebar:
        st.markdown(
            '<div class="mv-brand"><span class="mv-brand-mark">✦</span><span>MEMORY VAULT<small>YOUR LIFE, LOVINGLY KEPT</small></span></div>',
            unsafe_allow_html=True,
        )
        st.button(
            "＋  Create a memory",
            type="primary",
            width="stretch",
            on_click=lambda: setattr(st.session_state, "view", "Add memory"),
        )
        st.markdown("<div style='height:13px'></div><div class='mv-eyebrow' style='color:#a69bbd'>YOUR SPACE</div>", unsafe_allow_html=True)
        pages = ["Dashboard", "Timeline", "Memory capsules", "My story", "Privacy"]
        for label in pages:
            active = st.session_state.view == label
            if st.button(
                f"{'●' if active else '○'}  {label}",
                key=f"nav-{label}",
                width="stretch",
                type="primary" if active else "secondary",
                on_click=lambda selected=label: setattr(st.session_state, "view", selected),
            ):
                pass
        st.markdown("<div style='height:1px;background:#ffffff20;margin:17px 0'></div><div class='mv-eyebrow' style='color:#a69bbd'>COLLECTIONS</div>", unsafe_allow_html=True)
        counts = Counter(memory["category"] for memory in database.list_memories())
        for category in CATEGORIES[:5]:
            if st.button(
                f"{CATEGORY_ICONS[category]}  {category}   ·   {counts[category]}",
                key=f"category-{category}",
                width="stretch",
                on_click=lambda selected=category: (
                    setattr(st.session_state, "view", "Timeline"),
                    setattr(st.session_state, "timeline_category", selected),
                ),
            ):
                pass
        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        st.caption("🔒  Your memories stay in this database.")
        if not configured_password():
            st.warning("Set APP_PASSWORD in Streamlit secrets before sharing this app.")

    view = st.session_state.view
    if view == "Dashboard":
        render_dashboard()
    elif view == "Add memory":
        render_add_memory()
    elif view == "Timeline":
        render_timeline()
    elif view == "Memory capsules":
        render_capsules()
    elif view == "My story":
        render_story()
    else:
        render_privacy()
    st.markdown(
        '<div class="mv-footer"><span>Memory Vault · Preserve Moments. Relive Stories.</span><span>Private by design · Made to remember</span></div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()