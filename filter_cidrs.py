#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ipaddress
import logging
import sys
from pathlib import Path
from typing import Any

import yaml

log = logging.getLogger(__name__)


def load_yaml(path: Path) -> list[dict[str, Any]]:
    try:
        with open(path, "r") as f:
            data: Any = yaml.safe_load(f)
    except FileNotFoundError:
        log.error("File not found: %s", path)
        sys.exit(2)
    except PermissionError:
        log.error("Permission denied reading file: %s", path)
        sys.exit(2)
    except yaml.YAMLError as exc:
        log.error("Failed to parse YAML file %s: %s", path, exc)
        sys.exit(2)

    if not isinstance(data, dict):
        log.error("YAML file %s does not contain a mapping at the root level", path)
        sys.exit(2)

    if "laa_cidrs" not in data:
        log.error("Key 'laa_cidrs' not found in %s", path)
        sys.exit(2)

    cidrs = data["laa_cidrs"]

    if not isinstance(cidrs, list):
        log.error("'laa_cidrs' in %s is not a list", path)
        sys.exit(2)

    return cidrs


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Extract CIDRs from a YAML allowlist file by matching tag groups.\n\n"
            "Tag-matching logic:\n"
            "  Within a single --group, ALL tags must be present (AND).\n"
            "  Across multiple --group flags, ANY match is sufficient (OR).\n"
            "  Duplicate CIDRs in the output are automatically removed."
        ),
        epilog=(
            "examples:\n"
            "  Match CIDRs tagged with both 'external' AND 'staff':\n"
            "    %(prog)s --group external staff\n\n"
            "  Match CIDRs tagged 'external' OR 'internal' (separate groups):\n"
            "    %(prog)s --group external --group internal\n\n"
            "  Match ('external' AND 'staff') OR ('internal' AND 'vpn'):\n"
            "    %(prog)s --group external staff --group internal vpn\n\n"
            "  Use a custom YAML file:\n"
            "    %(prog)s --group external -f /path/to/custom.yaml\n\n"
            "  Show detailed matching information on stderr:\n"
            "    %(prog)s --group external --debug\n\n"
            "  Skip CIDR syntax validation (trusted inputs):\n"
            "    %(prog)s --group external --no-validate\n\n"
            "  Pipe matched CIDRs into another tool:\n"
            "    %(prog)s --group external staff | xargs -I{} echo {}\n\n"
            "  Write matched CIDRs to a file:\n"
            "    %(prog)s --group external staff -o cidrs.txt\n\n"
            "  List all available tags in the YAML file:\n"
            "    %(prog)s --list-tags"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-g", "--group",
        nargs="+",
        action="append",
        metavar="TAG",
        help=(
            "One or more tags that must ALL be present on a CIDR entry (AND). "
            "Repeat the flag to add alternative groups (OR). "
            "Required unless --list-tags is used. "
            "Example: --group external staff --group internal"
        ),
    )

    parser.add_argument(
        "-l", "--list-tags",
        action="store_true",
        help=(
            "Print all unique tags found in the YAML file, sorted alphabetically, "
            "then exit. Useful for discovering available tags before filtering."
        ),
    )

    parser.add_argument(
        "-f", "--file",
        default="laa-cidrs.yaml",
        metavar="PATH",
        help="Path to the YAML allowlist file (default: laa-cidrs.yaml).",
    )

    parser.add_argument(
        "-o", "--output",
        default=None,
        metavar="PATH",
        help="Write matched CIDRs to PATH instead of stdout.",
    )

    parser.add_argument(
        "-D", "--debug",
        action="store_true",
        help=(
            "Enable DEBUG-level logging to stderr. "
            "Shows each entry evaluated, its tags, and why it matched or was skipped."
        ),
    )

    parser.add_argument(
        "--no-validate",
        action="store_true",
        help=(
            "Skip IPv4/IPv6 CIDR syntax validation. "
            "Use on trusted inputs where validation overhead is unwanted."
        ),
    )

    args: argparse.Namespace = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.WARNING,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    if not args.list_tags and not args.group:
        parser.error("the following arguments are required: -g/--group")

    log.debug("Loading YAML file: %s", args.file)
    cidrs = load_yaml(Path(args.file))
    log.debug("Loaded %d entries from %s", len(cidrs), args.file)

    if args.list_tags:
        all_tags: set[str] = set()
        for item in cidrs:
            if not isinstance(item, dict):
                continue
            tags_raw = item.get("tags", [])
            if isinstance(tags_raw, list):
                all_tags.update(t for t in tags_raw if isinstance(t, str))
        for tag in sorted(all_tags):
            print(tag)
        return 0

    log.debug("Tag groups: %s", args.group)

    matched: dict[str, None] = {}

    for i, item in enumerate(cidrs):
        if not isinstance(item, dict):
            log.warning("Entry %d is not a mapping, skipping", i)
            continue

        if "cidr" not in item:
            log.warning("Entry %d missing 'cidr' key, skipping: %s", i, item)
            continue

        cidr = item["cidr"]

        if not isinstance(cidr, str):
            log.warning("Entry %d has non-string 'cidr' value (%r), skipping", i, cidr)
            continue

        tags_raw: list[Any] = item.get("tags", [])
        if not isinstance(tags_raw, list):
            log.warning("Entry %d has non-list 'tags' value, skipping: %s", i, item)
            continue

        non_str_tags: list[Any] = [t for t in tags_raw if not isinstance(t, str)]
        if non_str_tags:
            log.warning("Entry %d has non-string tag(s) %r, skipping", i, non_str_tags)
            continue

        if not args.no_validate:
            try:
                ipaddress.ip_network(cidr, strict=False)
            except ValueError:
                log.warning("Entry %d has invalid CIDR '%s', skipping", i, cidr)
                continue

        entry_tags: set[str] = set(tags_raw)
        log.debug("Entry %d: cidr=%s tags=%s", i, cidr, entry_tags)

        # OR across groups
        for group in args.group:
            # AND within group
            if set(group).issubset(entry_tags):
                log.debug("  -> matched group %s", group)
                matched[cidr] = None  # dict preserves insertion order and deduplicates
                break

    log.debug("Output: %d unique CIDR(s) matched", len(matched))

    if args.output:
        output_path = Path(args.output)
        try:
            output_path.write_text("".join(f"{cidr}\n" for cidr in matched))
        except (PermissionError, OSError) as exc:
            log.error("Failed to write output file %s: %s", output_path, exc)
            sys.exit(2)
        log.debug("Written %d CIDR(s) to %s", len(matched), output_path)
    else:
        for cidr in matched:
            print(cidr)

    return 0 if matched else 1


if __name__ == "__main__":
    sys.exit(main())
