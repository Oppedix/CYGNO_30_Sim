#!/usr/bin/env python3
"""Offline shell/transfer/submission-contract checks. No site or worker is contacted."""
from pathlib import Path
import subprocess
import sys
repo=Path(__file__).resolve().parents[1]
sys.exit(subprocess.call([sys.executable,'-m','unittest','discover','-s','tests','-p','test_condor.py','-v'],cwd=repo))
