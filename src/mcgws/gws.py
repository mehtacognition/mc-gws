"""Wrapper around the gws CLI for Google Workspace API calls."""

import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

GWS_BIN = Path.home() / ".local" / "bin" / "gws"


class GWSError(Exception):
    """Error from gws CLI call."""
    pass


def gws_call(*args, params: dict = None, json_body: dict = None,
             account: str = None, timeout: int = 30) -> dict:
    """Call gws CLI and return parsed JSON response.

    Args:
        *args: Positional args passed to gws (e.g., "drive", "files", "list").
        params: Query parameters (passed as --params JSON).
        json_body: Request body (passed as --json).
        account: Google account email (passed as --account).
        timeout: Subprocess timeout in seconds.

    Returns:
        Parsed JSON response dict.

    Raises:
        GWSError: If the gws command fails.
    """
    cmd = [str(GWS_BIN)] + list(args)

    if account:
        cmd.extend(["--account", account])
    if params:
        cmd.extend(["--params", json.dumps(params)])
    if json_body:
        cmd.extend(["--json", json.dumps(json_body)])

    logger.debug(f"gws call: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise GWSError(f"gws call timed out after {timeout}s: {' '.join(args)}")

    if result.returncode != 0:
        error_msg = result.stderr.strip() or result.stdout.strip()
        try:
            error_data = json.loads(error_msg)
            if "error" in error_data:
                error_msg = error_data["error"].get("message", error_msg)
        except (json.JSONDecodeError, TypeError):
            pass
        raise GWSError(error_msg)

    if not result.stdout.strip():
        return {}

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"raw": result.stdout.strip()}
