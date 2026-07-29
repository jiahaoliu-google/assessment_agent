"""
Terminal UI Utilities: ANSI formatting, banners, tables, and agent status logs.
"""

import sys
import time

# ANSI Escape Sequences
CLEAR = "\033[2J\033[H"
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"

# Foreground Colors
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
RED = "\033[31m"
WHITE = "\033[37m"
BRIGHT_CYAN = "\033[96m"
BRIGHT_GREEN = "\033[92m"
BRIGHT_YELLOW = "\033[93m"
BRIGHT_MAGENTA = "\033[95m"


def print_banner():
    """Prints the application banner to stdout."""
    banner = f"""
{BRIGHT_CYAN}{BOLD}================================================================================={RESET}
{BRIGHT_CYAN}{BOLD}                🥗 MULTI-AGENT INTELLIGENT MEAL PLANNER SYSTEM 🥗               {RESET}
{CYAN}        Autonomous Multi-Agent Collaboration for Personalized 7-Day Nutrition    {RESET}
{BRIGHT_CYAN}{BOLD}================================================================================={RESET}
"""
    print(banner)


def print_agent_header(agent_name: str, role_desc: str, color: str = BRIGHT_CYAN):
    """Prints a styled header for an agent step."""
    border = "-" * 75
    print(f"\n{color}{BOLD}🤖 [{agent_name}] {RESET}{DIM}- {role_desc}{RESET}")
    print(f"{color}{border}{RESET}")


def log_agent_action(agent_name: str, action_desc: str, color: str = BRIGHT_GREEN):
    """Outputs a live agent activity line."""
    timestamp = time.strftime("%H:%M:%S")
    print(f"  {DIM}[{timestamp}]{RESET} {color}{BOLD}► [{agent_name}]{RESET} {action_desc}")


def print_box(title: str, text_lines: list, color: str = CYAN, width: int = 75):
    """Draws a nice Unicode box containing text lines."""
    top = f"┌─ {BOLD}{title}{RESET}{color} " + "─" * (width - len(title) - 4) + "┐"
    bottom = "└" + "─" * (width - 2) + "┘"
    print(f"{color}{top}{RESET}")
    for line in text_lines:
        padded = line + " " * max(0, width - 4 - len_without_ansi(line))
        print(f"{color}│{RESET} {padded} {color}│{RESET}")
    print(f"{color}{bottom}{RESET}")


def len_without_ansi(s: str) -> int:
    """Helper to calculate string length excluding ANSI escape codes."""
    import re
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return len(ansi_escape.sub('', s))


def print_table(headers: list, rows: list, column_widths: list = None):
    """Renders a structured table with borders."""
    if not column_widths:
        column_widths = [max(len_without_ansi(str(row[i])) for row in [headers] + rows) + 2 for i in range(len(headers))]

    header_str = "│ " + " │ ".join(f"{BOLD}{str(headers[i]).ljust(column_widths[i])}{RESET}" for i in range(len(headers))) + " │"
    divider = "├─" + "─┼─".join("─" * w for w in column_widths) + "─┤"
    top_border = "┌─" + "─┬─".join("─" * w for w in column_widths) + "─┐"
    bottom_border = "└─" + "─┴─".join("─" * w for w in column_widths) + "─┘"

    print(CYAN + top_border + RESET)
    print(header_str)
    print(CYAN + divider + RESET)
    for row in rows:
        row_str = "│ " + " │ ".join(f"{str(row[i]).ljust(column_widths[i])}" for i in range(len(row))) + " │"
        print(row_str)
    print(CYAN + bottom_border + RESET)
