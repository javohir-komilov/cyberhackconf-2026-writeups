#!/usr/bin/env python3
import os, sys

FLAG = os.environ.get('FLAG', '000000000000000000000000')

BANNER = """
╔══════════════════════════════════════════════════════════╗
║           AN INNOCENT EMPLOYEE - FORENSICS               ║
║  Analyze the disk image and answer all questions.        ║
║  Download: https://drive.google.com/drive/folders/       ║
║    1LBbWdpT5d9pOXOmUBjbquZuRygcrhSIn                    ║
╚══════════════════════════════════════════════════════════╝
"""

QA = [
    (
        "Q1: What is the name of the application in which the\n"
        "    conversation took place between the attacker and victim?\n> ",
        "discord"
    ),
    (
        "Q2: What are their usernames?\n"
        "    Format: @attacker:@victim\n> ",
        "@johnysainz_94219:@bob_12331"
    ),
    (
        "Q3: When was the malicious link sent?\n"
        "    Format: YYYY-MM-DD HH:MM:SS UTC\n> ",
        "2025-12-18 16:00:45 utc"
    ),
    (
        "Q4: What is the required password?\n> ",
        "ycyu9nsrj2"
    ),
    (
        "Q5: What file sharing service was used to host the malicious file?\n> ",
        "mega.nz"
    ),
    (
        "Q6: What is the SHA256 hash of the malicious file?\n> ",
        "8f16da672b72afa99e534d022b945bdc8a4ea1083d09ba7930df2dd163eb3bb8"
    ),
    (
        "Q7: Which malware family does this sample belong to?\n> ",
        "infostealer"
    ),
]

def main():
    sys.stdout.write(BANNER + "\n")
    sys.stdout.flush()

    for i, (prompt, answer) in enumerate(QA):
        sys.stdout.write(prompt)
        sys.stdout.flush()
        try:
            user_input = sys.stdin.readline().strip()
        except (EOFError, KeyboardInterrupt):
            sys.stdout.write("\nBye!\n")
            sys.stdout.flush()
            return

        if user_input.lower() == answer.lower():
            sys.stdout.write("  ✓ Correct!\n\n")
            sys.stdout.flush()
        else:
            sys.stdout.write(f"  ✗ Incorrect. Better luck next time!\n")
            sys.stdout.flush()
            return

    flag = f"CHC{{an_innocent_employee_{FLAG}}}"
    sys.stdout.write(f"\n🎉 All correct! Here is your flag:\n{flag}\n")
    sys.stdout.flush()

if __name__ == "__main__":
    main()
