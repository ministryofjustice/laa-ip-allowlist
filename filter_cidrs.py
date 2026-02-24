#!/usr/bin/env python3

import argparse
import logging
import sys
import yaml
from pathlib import Path

log = logging.getLogger(__name__)


def load_yaml(path: Path):
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        log.error("File not found: %s", path)
        sys.exit(1)
    except PermissionError:
        log.error("Permission denied reading file: %s", path)
        sys.exit(1)
    except yaml.YAMLError as exc:
        log.error("Failed to parse YAML file %s: %s", path, exc)
        sys.exit(1)


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

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging to stderr"
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.WARNING,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    log.debug("Loading YAML file: %s", args.file)
    data = load_yaml(Path(args.file))

    if not isinstance(data, dict):
        log.error("YAML file %s does not contain a mapping at the root level", args.file)
        sys.exit(1)

    if "laa_cidrs" not in data:
        log.error("Key 'laa_cidrs' not found in %s", args.file)
        sys.exit(1)

    cidrs = data["laa_cidrs"]

    if not isinstance(cidrs, list):
        log.error("'laa_cidrs' in %s is not a list", args.file)
        sys.exit(1)

    log.debug("Loaded %d entries from %s", len(cidrs), args.file)
    log.debug("Tag groups: %s", args.group)

    for i, item in enumerate(cidrs):
        if not isinstance(item, dict):
            log.warning("Entry %d is not a mapping, skipping", i)
            continue

        if "cidr" not in item:
            log.warning("Entry %d missing 'cidr' key, skipping: %s", i, item)
            continue

        tags_raw = item.get("tags", [])
        if not isinstance(tags_raw, list):
            log.warning("Entry %d has non-list 'tags' value, skipping: %s", i, item)
            continue

        entry_tags = set(tags_raw)
        log.debug("Entry %d: cidr=%s tags=%s", i, item["cidr"], entry_tags)

        # OR across groups
        for group in args.group:
            # AND within group
            if set(group).issubset(entry_tags):
                log.debug("  -> matched group %s", group)
                print(item["cidr"])
                break


if __name__ == "__main__":
    main()
