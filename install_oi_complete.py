# -*- coding: utf-8 -*-
"""
PHANTOM GRID OpenCode / OI 雙模一鍵安裝與自適應配置凍結器 (install_oi_complete.py)
"""

import sys
from pathlib import Path

# Windows UTF-8 強制防護
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from install_opencode_complete import main

if __name__ == "__main__":
    print("🤖 [PHANTOM GRID · OI / OpenCode 一鍵安裝與配置凍結總控]")
    main()
