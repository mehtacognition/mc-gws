"""Drive, Docs, and Sheets commands — fast path, no LLM."""

from mcgws.config import load_config
from mcgws.gws import gws_call
from mcgws.formatting import format_drive_file


def _get_config():
    return load_config()


def run(args: list):
    """Execute drive subcommand."""
    config = _get_config()
    account = config["account"]

    if not args:
        print("Usage: g drive \"query\" | g drive recent")
        return

    if args[0] == "recent":
        result = gws_call(
            "drive", "files", "list",
            params={"pageSize": 15, "orderBy": "modifiedTime desc"},
            account=account,
        )
    else:
        query = " ".join(args)
        result = gws_call(
            "drive", "files", "list",
            params={"q": f"name contains '{query}' or fullText contains '{query}'", "pageSize": 15},
            account=account,
        )

    files = result.get("files", [])
    if not files:
        print("No files found.")
        return

    label = "recent files" if args[0] == "recent" else f"results for \"{' '.join(args)}\""
    print(f"\n📁 Drive — {len(files)} {label}\n")
    for f in files:
        print(format_drive_file(f))
    print()


def run_docs(args: list):
    """Search Google Docs specifically."""
    config = _get_config()
    account = config["account"]

    if not args:
        print("Usage: g docs \"query\"")
        return

    query = " ".join(args)
    result = gws_call(
        "drive", "files", "list",
        params={
            "q": f"mimeType='application/vnd.google-apps.document' and (name contains '{query}' or fullText contains '{query}')",
            "pageSize": 15,
        },
        account=account,
    )
    files = result.get("files", [])
    if not files:
        print(f"No docs matching: {query}")
        return

    print(f"\n📄 Docs — {len(files)} results for \"{query}\"\n")
    for f in files:
        print(format_drive_file(f))
    print()


def run_sheets(args: list):
    """Show spreadsheet summary."""
    config = _get_config()
    account = config["account"]

    if not args:
        print("Usage: g sheets <spreadsheet_id>")
        return

    sheet_id = args[0]
    result = gws_call(
        "sheets", "spreadsheets", "get",
        params={"spreadsheetId": sheet_id},
        account=account,
    )
    title = result.get("properties", {}).get("title", "Untitled")
    sheets = result.get("sheets", [])
    print(f"\n📊 {title}\n")
    for s in sheets:
        props = s.get("properties", {})
        name = props.get("title", "Sheet")
        rows = props.get("gridProperties", {}).get("rowCount", 0)
        cols = props.get("gridProperties", {}).get("columnCount", 0)
        print(f"  {name} ({rows} rows x {cols} cols)")
    print()
