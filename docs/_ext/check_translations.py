"""Update or validate Chinese gettext catalogs against a fresh Sphinx extraction."""

from __future__ import annotations

import argparse
from pathlib import Path

from babel.messages.catalog import Catalog
from babel.messages.pofile import read_po, write_po

DOCS = Path(__file__).resolve().parents[1]
LOCALE = DOCS / "locale/zh_CN/LC_MESSAGES"


def check_translations(templates: Path, update: bool = False) -> None:
    """Reject missing, fuzzy, obsolete, or invalid catalog entries."""
    errors = []
    pots = sorted(templates.glob("*.pot"))
    if not pots:
        raise ValueError(f"No Sphinx gettext templates found in {templates}")
    for pot in pots:
        with pot.open("rb") as stream:
            template = read_po(stream)
        po = LOCALE / pot.with_suffix(".po").name
        if po.is_file():
            with po.open("rb") as stream:
                catalog = read_po(stream, locale="zh_CN")
        elif update:
            catalog = Catalog(locale="zh_CN", project="pymecheye")
            catalog.fuzzy = False
        else:
            errors.append(f"Missing catalog: {po}")
            continue
        if update:
            catalog.update(template, no_fuzzy_matching=True)
            catalog.obsolete.clear()
            # Keep catalog source references portable across checkout and build paths.
            for message in catalog:
                locations = []
                for name, line in message.locations:
                    name = name.replace("\\", "/")
                    marker = DOCS.parent.as_posix() + "/"
                    if marker in name:
                        name = name.split(marker, 1)[1]
                    if name != "of":
                        locations.append((name, line))
                message.locations = locations
            LOCALE.mkdir(parents=True, exist_ok=True)
            with po.open("wb") as stream:
                write_po(
                    stream, catalog, width=88, omit_header=False, include_previous=False
                )
            continue
        if catalog.fuzzy:
            errors.append(f"{po.name}: catalog header is fuzzy")
        expected = {message.id for message in template if message.id}
        actual = {message.id for message in catalog if message.id}
        for msgid in sorted(expected - actual):
            errors.append(f"{po.name}: missing {msgid!r}")
        for msgid in sorted(actual - expected):
            errors.append(f"{po.name}: stale {msgid!r}")
        for message in catalog:
            if message.id and (not message.string or "fuzzy" in message.flags):
                errors.append(f"{po.name}: untranslated or fuzzy {message.id!r}")
        if catalog.obsolete:
            errors.append(f"{po.name}: obsolete entries must be removed")
        for message, issues in catalog.check():
            errors.append(f"{po.name}: invalid {message.id!r}: {issues}")
    if errors:
        raise ValueError("Translation catalogs need attention:\n" + "\n".join(errors))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("templates", type=Path)
    parser.add_argument("--update", action="store_true")
    args = parser.parse_args()
    check_translations(args.templates, update=args.update)
