"""The dense Matrix desk on the home page.

Windows sit in three columns. A window that has nothing to show is left out and the windows below it move
up, so the desk never has holes (for example before GitHub is connected).
"""
from web import live

TOP = 20
GAP = 20
DOCK_SPACE = 96  # room under the columns for the dock

# (x, w, [(window, height), ...]) per column, top to bottom.
COLUMNS = (
    ("2%", "37%", (("about", 350), ("graph", 200), ("stack", 230))),
    ("40.5%", "33%", (("terminal", 250), ("projects", 220), ("activity", 190))),
    ("75%", "23%", (("now", 250), ("links", 170), ("stats", 220))),
)
STAGGER_MS = 70


def desk_layout(shown):
    """{"height": px, "windows": {name: {"x", "y", "w", "h", "delay"}}} for the windows marked shown."""
    windows, bottoms = {}, []
    for col, (x, w, stack) in enumerate(COLUMNS):
        y = TOP
        for row, (name, h) in enumerate(stack):
            if not shown.get(name):
                continue
            windows[name] = {"x": x, "y": y, "w": w, "h": h, "delay": (row * len(COLUMNS) + col) * STAGGER_MS}
            y += h + GAP
        bottoms.append(y - GAP)
    return {"height": max(bottoms) + DOCK_SPACE, "windows": windows}


def terminal_transcript(profile, project_count, events):
    """The session the terminal window types out: real commands with real output, nothing invented."""
    lines = ["$ whoami", f"{profile.handle or profile.name}" + (f" — {profile.headline}" if profile.headline else "")]
    if profile.location:
        lines += ["$ cat ~/.location", profile.location]
    lines += ["$ ls ~/projects | wc -l", str(project_count)]
    texts = [live.describe_event(e)[0] for e in events[:3]]
    texts = [t for t in texts if t]
    if texts:
        lines += ["$ tail -n 3 ~/activity.log", *texts]
    status = live.availability(profile)["label"]
    if status:
        lines += ["$ status", status]
    return "\n".join(line.replace("\n", " ") for line in lines)


def stack_config(skills):
    """Skills as stack.cfg sections: [(group, [names])] in their stored order; ungrouped ones go under misc."""
    groups = {}
    for skill in skills:
        groups.setdefault((skill.group or "misc").strip().lower(), []).append(skill.name)
    return list(groups.items())
