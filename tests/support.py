"""Shared test helpers."""


def idea_script(project, channel, title="S"):
    """A script made from an idea: the quickest material a script can have."""
    idea = next((i for i in project.ideas() if i["title"] == title), None)
    if not idea:
        project.add_ideas([{"title": title, "pitch": "What the video answers.", "signal": {"kind": "agent", "detail": "A test idea"}}])
        idea = next(i for i in project.ideas() if i["title"] == title)
    return project.create_script(channel, idea_id=idea["id"])
