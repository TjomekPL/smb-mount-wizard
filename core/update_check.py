import json
import urllib.request

REPO_API_URL = "https://api.github.com/repos/TjomekPL/smb-mount-wizard/tags"


def _parse_version(v):
    parts = v.split(".")
    nums = []
    for p in parts:
        try:
            nums.append(int(p))
        except ValueError:
            nums.append(0)
    return tuple(nums)


def get_latest_version_tag(timeout=5):
    """
    Returns the latest version tag from GitHub (e.g. "0.7.0", without
    the leading 'v'), or None if it can't be determined - offline,
    repo private/inaccessible, no tags yet, rate limited, etc.

    Never raises. Requires the repo to be PUBLIC - the GitHub API
    needs an auth token to read tags on a private repo, which this
    intentionally does not store/handle.
    """
    try:
        req = urllib.request.Request(
            REPO_API_URL,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "smb-mount-wizard",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())

        if not data:
            return None

        names = [t.get("name", "").lstrip("v") for t in data if t.get("name")]
        names = [n for n in names if n]

        if not names:
            return None

        names.sort(key=_parse_version)
        return names[-1]

    except Exception:
        return None


def is_newer(remote, local):
    """
    True if 'remote' (e.g. "0.8.0") is a newer version than 'local'.
    """
    try:
        return _parse_version(remote) > _parse_version(local)
    except Exception:
        return False
