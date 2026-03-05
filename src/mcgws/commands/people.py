"""People/contacts command — fast path, no LLM."""

from mcgws.config import load_config
from mcgws.gws import gws_call


def _get_config():
    return load_config()


def run(args: list):
    """Search contacts via Google People API."""
    config = _get_config()
    account = config["account"]

    if not args:
        print("Usage: g people \"name\"")
        return

    query = " ".join(args)
    result = gws_call(
        "people", "people", "searchContacts",
        params={"query": query, "readMask": "names,emailAddresses,phoneNumbers,organizations"},
        account=account,
    )
    results = result.get("results", [])
    if not results:
        print(f"No contacts matching: {query}")
        return

    print(f"\n👤 Contacts — {len(results)} results for \"{query}\"\n")
    for r in results:
        person = r.get("person", {})
        names = person.get("names", [{}])
        name = names[0].get("displayName", "Unknown") if names else "Unknown"
        emails = person.get("emailAddresses", [])
        phones = person.get("phoneNumbers", [])
        orgs = person.get("organizations", [])

        print(f"  {name}")
        for e in emails:
            print(f"    Email: {e.get('value', '')}")
        for p in phones:
            print(f"    Phone: {p.get('value', '')}")
        for o in orgs:
            title = o.get("title", "")
            company = o.get("name", "")
            if title and company:
                print(f"    {title} at {company}")
            elif company:
                print(f"    {company}")
    print()
