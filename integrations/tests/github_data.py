"""Canned GitHub API responses for tests."""
import json

import httpx

GRAPHQL = "https://api.github.com/graphql"


def repo_node(db_id, name, *, owner="A1isherDev", description="", fork=False, archived=False, languages=None, topics=None, pushed="2026-11-01T10:00:00Z", homepage=""):
    languages = languages if languages is not None else [("Python", 9000), ("HTML", 1000)]
    return {
        "databaseId": db_id,
        "name": name,
        "nameWithOwner": f"{owner}/{name}",
        "description": description,
        "url": f"https://github.com/{owner}/{name}",
        "homepageUrl": homepage,
        "stargazerCount": 3,
        "forkCount": 1,
        "isFork": fork,
        "isArchived": archived,
        "pushedAt": pushed,
        "primaryLanguage": {"name": languages[0][0]} if languages else None,
        "languages": {"edges": [{"size": size, "node": {"name": lang}} for lang, size in languages]},
        "repositoryTopics": {"nodes": [{"topic": {"name": t}} for t in (topics or [])]},
    }


def repos_page(nodes, *, next_cursor=None):
    return {
        "data": {
            "viewer": {
                "repositories": {
                    "pageInfo": {"hasNextPage": bool(next_cursor), "endCursor": next_cursor},
                    "nodes": nodes,
                }
            }
        }
    }


def viewer_profile(*, login="A1isherDev", pinned_ids=(), days=None):
    days = days or [
        {"date": "2026-11-08", "contributionCount": 0, "contributionLevel": "NONE"},
        {"date": "2026-11-09", "contributionCount": 4, "contributionLevel": "SECOND_QUARTILE"},
        {"date": "2026-11-10", "contributionCount": 12, "contributionLevel": "FOURTH_QUARTILE"},
    ]
    return {
        "data": {
            "viewer": {
                "login": login,
                "pinnedItems": {"nodes": [{"databaseId": i} for i in pinned_ids]},
                "contributionsCollection": {
                    "contributionCalendar": {
                        "totalContributions": sum(d["contributionCount"] for d in days),
                        "weeks": [{"contributionDays": days}],
                    }
                },
            }
        }
    }


def query_of(request):
    return json.loads(request.content.decode())["query"]


def install_graphql(api, *, repos_pages, profile):
    """Answer the profile query and the paginated repositories query."""
    pages = list(repos_pages)

    def respond(request):
        body = json.loads(request.content.decode())
        if "pinnedItems" in body["query"]:
            return httpx.Response(200, json=profile)
        after = (body.get("variables") or {}).get("after")
        index = 0 if after is None else int(after)
        return httpx.Response(200, json=pages[index])

    api.add("POST", GRAPHQL, respond)
