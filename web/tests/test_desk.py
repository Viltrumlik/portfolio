"""The dense Matrix desk on the home page: layout, the terminal transcript and stack.cfg."""
from types import SimpleNamespace

import pytest

from content.models import Profile, Skill
from web import desk

ALL = {key: True for key in ("about", "terminal", "now", "graph", "projects", "links", "stack", "activity", "stats")}


def test_layout_places_every_shown_window_in_three_columns():
    layout = desk.desk_layout(ALL)
    wins = layout["windows"]
    assert set(wins) == set(ALL)
    assert {wins[k]["x"] for k in ("about", "graph", "stack")} == {"2%"}
    assert {wins[k]["x"] for k in ("terminal", "projects", "activity")} == {"40.5%"}
    assert {wins[k]["x"] for k in ("now", "links", "stats")} == {"75%"}
    assert wins["about"]["y"] == desk.TOP
    assert wins["graph"]["y"] == desk.TOP + wins["about"]["h"] + desk.GAP


def test_hidden_windows_leave_no_gap_in_their_column():
    layout = desk.desk_layout({**ALL, "graph": False, "activity": False})
    wins = layout["windows"]
    assert "graph" not in wins and "activity" not in wins
    assert wins["stack"]["y"] == desk.TOP + wins["about"]["h"] + desk.GAP
    assert wins["stats"]["y"] > wins["links"]["y"]


def test_desk_height_fits_the_tallest_column_plus_the_dock():
    layout = desk.desk_layout(ALL)
    bottoms = [w["y"] + w["h"] for w in layout["windows"].values()]
    assert layout["height"] == max(bottoms) + desk.DOCK_SPACE


def test_windows_switch_on_row_by_row():
    wins = desk.desk_layout(ALL)["windows"]
    assert wins["about"]["delay"] < wins["terminal"]["delay"] < wins["now"]["delay"] < wins["graph"]["delay"]


def test_stack_config_groups_skills_in_order():
    skills = [SimpleNamespace(group="Backend", name="Django"), SimpleNamespace(group="Backend", name="DRF"),
              SimpleNamespace(group="", name="Git"), SimpleNamespace(group="Frontend", name="React")]
    assert desk.stack_config(skills) == [("backend", ["Django", "DRF"]), ("misc", ["Git"]), ("frontend", ["React"])]


@pytest.mark.django_db
def test_terminal_transcript_types_commands_and_their_real_output():
    profile = Profile.load()
    profile.handle, profile.headline, profile.location = "viltrumlik", "Backend engineer", "Tashkent, Uzbekistan"
    profile.availability = Profile.Availability.AVAILABLE
    profile.availability_note = "Open to work"
    events = [SimpleNamespace(type="github.push", payload={"repo": "me/atlas", "commits": 3})]
    lines = desk.terminal_transcript(profile, project_count=12, events=events).split("\n")
    assert lines[:2] == ["$ whoami", "viltrumlik — Backend engineer"]
    assert "Tashkent, Uzbekistan" in lines
    assert lines[lines.index("$ ls ~/projects | wc -l") + 1] == "12"
    assert "Pushed 3 commits to me/atlas" in lines
    assert lines[-2:] == ["$ status", "Open to work"]
    assert all(line.strip() for line in lines)


@pytest.mark.django_db
def test_terminal_transcript_skips_what_it_does_not_know():
    profile = Profile.load()
    profile.location = ""
    profile.availability = Profile.Availability.HIDDEN
    text = desk.terminal_transcript(profile, project_count=0, events=[])
    assert "~/.location" not in text and "activity.log" not in text and "$ status" not in text


@pytest.mark.django_db
def test_stack_config_reads_skills_from_the_database():
    Skill.objects.create(group="Backend", name="Django", order=1)
    assert desk.stack_config(Skill.objects.all()) == [("backend", ["Django"])]
