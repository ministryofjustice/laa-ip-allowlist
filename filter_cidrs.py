#!/usr/bin/env python3

import argparse
import yaml
from pathlib import Path


def load_yaml(path: Path):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Extract CIDRs using tag groups (AND inside group, OR between groups)"
    )

    parser.add_argument(
        "--group",
        nargs="+",
        action="append",
        required=True,
        help="Tag group. Repeatable. Example: --group external staff"
    )

    parser.add_argument(
        "-f", "--file",
        default="laa-cidrs.yaml",
        help="Path to YAML file"
    )

    args = parser.parse_args()

    data = load_yaml(Path(args.file))
    cidrs = data.get("laa_cidrs", [])

    for item in cidrs:
        entry_tags = set(item.get("tags", []))

        # OR across groups
        for group in args.group:
            # AND within group
            if set(group).issubset(entry_tags):
                print(item["cidr"])
                break


if __name__ == "__main__":
    main()
