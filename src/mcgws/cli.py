"""CLI entry point for the g command."""

import sys
import warnings
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL")


USAGE = """Usage: g <command> [args...]

Smart Path (LLM-powered):
  briefing              Strategic morning digest
  midday                Midday check-in
  prep "meeting"        Meeting preparation
  wrap                  End-of-day summary
  weekly                Monday week-ahead overview
  chat "query"          Freeform chief of staff

Fast Path (instant):
  calendar [today|tomorrow|week]   Calendar view
  calendar add "title" day time    Create event
  calendar conflicts               Show conflicts
  email                            Recent unread
  email "query"                    Search email
  email read <id>                  Read email
  email reply <id> "body"          Reply to thread
  email send "to" "subj" "body"    Send email
  email forward <id> "to"          Forward email
  email draft "to" "subj" "body"   Create draft
  email label <id> "label"         Label email
  email archive <id>               Archive email
  drive "query"                    Search Drive
  drive recent                     Recent files
  docs "query"                     Search Docs
  sheets <id>                      Spreadsheet summary
  search "query"                   Unified search
  tasks                            List Google Tasks
  tasks add "title"                Quick-capture task
  people "name"                    Contact lookup
  followups                        Show follow-ups
  followups add "desc" [--due D]   Add follow-up
"""


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(USAGE)
        sys.exit(0)

    cmd = args[0]
    cmd_args = args[1:]

    # Dispatch to subcommand modules (to be implemented)
    try:
        if cmd == "calendar":
            from mcgws.commands.calendar import run
            run(cmd_args)
        elif cmd == "email":
            from mcgws.commands.email import run
            run(cmd_args)
        elif cmd == "drive":
            from mcgws.commands.drive import run
            run(cmd_args)
        elif cmd == "docs":
            from mcgws.commands.drive import run_docs
            run_docs(cmd_args)
        elif cmd == "sheets":
            from mcgws.commands.drive import run_sheets
            run_sheets(cmd_args)
        elif cmd == "search":
            from mcgws.commands.search import run
            run(cmd_args)
        elif cmd == "tasks":
            from mcgws.commands.tasks import run
            run(cmd_args)
        elif cmd == "people":
            from mcgws.commands.people import run
            run(cmd_args)
        elif cmd == "followups":
            from mcgws.commands.followups import run
            run(cmd_args)
        elif cmd == "briefing":
            from mcgws.commands.smart import run_briefing
            run_briefing(cmd_args)
        elif cmd == "midday":
            from mcgws.commands.smart import run_midday
            run_midday(cmd_args)
        elif cmd == "prep":
            from mcgws.commands.smart import run_prep
            run_prep(cmd_args)
        elif cmd == "wrap":
            from mcgws.commands.smart import run_wrap
            run_wrap(cmd_args)
        elif cmd == "weekly":
            from mcgws.commands.smart import run_weekly
            run_weekly(cmd_args)
        elif cmd == "chat":
            from mcgws.commands.smart import run_chat
            run_chat(cmd_args)
        else:
            print(f"Unknown command: {cmd}")
            print(USAGE)
            sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
