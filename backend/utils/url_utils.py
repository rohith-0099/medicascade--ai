"""Helpers for turning filesystem paths into URLs served by the app."""


def format_url(path: str) -> str:
    """Map a generated-artifact path to a URL under the ``/outputs`` mount.

    Returns an empty string for falsy input. Paths already containing an
    ``/outputs/`` segment are truncated to start there; everything else is
    served from the application root.
    """
    if not path:
        return ""
    clean_path = path.replace("\\", "/")
    if clean_path.startswith("outputs/"):
        return "/" + clean_path
    marker = "/outputs/"
    if marker in clean_path:
        return clean_path[clean_path.index(marker):]
    return "/" + clean_path
