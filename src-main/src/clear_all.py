#!/usr/bin/env python3
"""
Cleanup script to remove the 'case' folder 
"""
import shutil
from pathlib import Path

def remove_if_exists(path: Path, name: str):
    if path.exists() and path.is_dir():
        shutil.rmtree(path)
        print(f"🗑️  Deleted: {name}")
    else:
        print(f"ℹ️  Not found: {name}")


def main():
    script_dir = Path(__file__).resolve().parent
    case_dir = script_dir / 'case'

    print("🚨 This will permanently delete the following folder:")
    print(f"- {case_dir}")
    confirm = input("Are you sure? [y/N]: ").strip().lower()
    if confirm == 'y':
        remove_if_exists(case_dir, 'case/')
        print("✅ Cleanup complete.")
    else:
        print("❌ Aborted by user.")

if __name__ == '__main__':
    main()
