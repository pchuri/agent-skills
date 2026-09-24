#!/usr/bin/env python3
"""
Inspect Meta Muse Code CLI usage by running interactive TUI in a pseudo-terminal.
"""

import fcntl
import os
import pty
import re
import select
import struct
import sys
import termios
import time


def get_muse_usage(timeout_sec=15):
    master, slave = pty.openpty()
    pid = os.fork()

    if pid == 0:
        os.close(master)
        os.setsid()
        # Set terminal window size: 35 rows, 120 cols
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 35, 120, 0, 0))
        os.dup2(slave, 0)
        os.dup2(slave, 1)
        os.dup2(slave, 2)
        os.close(slave)
        os.environ['TERM'] = 'xterm-256color'
        os.environ['COLORTERM'] = 'truecolor'
        os.execlp('muse', 'muse', '--trust-workspace')
    else:
        os.close(slave)
        full_output = b''
        step = 0
        start_time = time.time()

        while time.time() - start_time < timeout_sec:
            r, _, _ = select.select([master], [], [], 0.05)
            if r:
                try:
                    data = os.read(master, 4096)
                    if not data:
                        break
                    full_output += data
                    # Respond to terminal queries
                    if b'\x1b[6n' in data:
                        os.write(master, b'\x1b[1;1R')
                    if b'\x1b[?c' in data or b'\x1b[c' in data:
                        os.write(master, b'\x1b[?1;2c')
                except OSError:
                    break

            elapsed = time.time() - start_time
            if step == 0 and elapsed > 2.0:
                os.write(master, b'/usage')
                step = 1
            elif step == 1 and elapsed > 2.8:
                os.write(master, b'\r')
                step = 2
            elif step == 2 and elapsed > 3.6:
                os.write(master, b'\r')
                step = 3

            # Check if full box has appeared
            if b'Weekly' in full_output and (b'as of' in full_output or b'\xe2\x94\x98' in full_output):
                time.sleep(0.5)
                r, _, _ = select.select([master], [], [], 0.2)
                if r:
                    try:
                        extra = os.read(master, 4096)
                        full_output += extra
                    except OSError:
                        pass
                break

        try:
            os.kill(pid, 9)
        except Exception:
            pass

        # Parse text
        text = full_output.decode('utf-8', errors='ignore')
        # Remove ANSI escape sequences
        clean_text = re.sub(
            r'\x1b\[[0-9;?]*[a-zA-Z]|\x1b\([a-zA-Z]|\x1b\].*?\x07|\x1b[=>]',
            '',
            text,
        )

        match = re.search(r'(┌[─\s\S]*?└[─\s\S]*?┘)', clean_text)
        if match:
            box = match.group(1).strip()
            # Insert newlines between borders
            box = box.replace('┐│', '┐\n│').replace('││', '│\n│').replace('│└', '│\n└')
            return box

        # Fallback: scan lines
        lines = [line.strip() for line in clean_text.splitlines() if line.strip()]
        relevant = [l for l in lines if any(k in l for k in ['Session usage', 'Subscription', 'Current', 'Weekly', 'as of'])]
        if relevant:
            return '\n'.join(relevant)

        return clean_text.strip()


def main():
    result = get_muse_usage()
    print(result)


if __name__ == '__main__':
    main()
