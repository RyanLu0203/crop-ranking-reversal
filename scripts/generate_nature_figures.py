#!/usr/bin/env python3
"""Regenerate the complete Issue 8 Nature visual system."""

from argparse import ArgumentParser
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"visualization/src"))

from crop_visualization.nature_figures import generate  # noqa: E402


if __name__ == "__main__":
    parser=ArgumentParser()
    parser.add_argument("--output-root",type=Path)
    args=parser.parse_args()
    generate(ROOT,args.output_root)
