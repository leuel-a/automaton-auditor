#!/usr/bin/env python3
"""A small interactive command-line interface built on Python's `cmd` module."""

from __future__ import annotations

import cmd
import shlex

from src.agent import AutomatonAuditorAgent


class AutomatonAuditorCLI(cmd.Cmd):
    """Interactive shell for Automaton Auditor."""

    intro = "Welcome to Automaton Auditor. Type help or ? to list commands.\n"
    prompt = "(auditor) "

    def __init__(self) -> None:
        self.agent = AutomatonAuditorAgent.create()
        super().__init__()

    def do_start(self, arg: str) -> None:
        """Start an audit session."""
        try:
            args = shlex.split(arg)
            if len(args) != 2:
                print("Usage: start <github_repo_url> <pdf_report_path>")
                return
        except ValueError:
            print("Invalid input: unmatched quotes. Example:")
            print('  start https://github.com/user/repo "My Reports/audit report.pdf"')
            return

        repo_url, pdf_path = args[0], args[1]
        self.agent.run(repo_url, pdf_path)

    def do_exit(self, _: str) -> bool:
        """Exit the CLI"""
        return True

    def do_quit(self, arg: str) -> bool:
        """Alias for exit."""
        return self.do_exit(arg)

    def do_EOF(self, _: str) -> bool:
        """Exit on Ctrl-D / EOF."""
        print()
        return True


def main():
    AutomatonAuditorCLI().cmdloop()


if __name__ == "__main__":
    main()
