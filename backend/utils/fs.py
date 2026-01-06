"""Filesystem helpers, including zip-slip / zip-bomb safe extraction."""
import re
import zipfile
from pathlib import Path

from backend.core.exceptions import ValidationAppError

_SLUG_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def slugify(value: str) -> str:
    value = value.strip().rstrip("/")
    value = value.rsplit("/", 1)[-1]
    if value.endswith(".git"):
        value = value[: -len(".git")]
    value = _SLUG_RE.sub("-", value).strip("-")
    return value or "repository"


def safe_extract_zip(zip_path: Path, dest_dir: Path, max_total_bytes: int) -> None:
    """Extract a zip archive into dest_dir, guarding against zip-slip and zip bombs.

    - Rejects entries whose resolved path would land outside dest_dir (zip slip).
    - Rejects absolute paths and symlink entries.
    - Rejects archives whose total uncompressed size exceeds max_total_bytes,
      to avoid a small upload expanding into an unbounded amount of disk I/O.
    """
    dest_dir = dest_dir.resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path) as archive:
        total_uncompressed = sum(member.file_size for member in archive.infolist())
        if total_uncompressed > max_total_bytes:
            raise ValidationAppError("Archive exceeds the maximum allowed extracted size")

        for member in archive.infolist():
            if member.is_dir():
                continue

            # Unix symlink bit in the high 16 bits of external_attr.
            is_symlink = (member.external_attr >> 16) & 0o170000 == 0o120000
            if is_symlink:
                continue

            member_path = Path(member.filename)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise ValidationAppError(f"Unsafe path in archive: {member.filename}")

            target = (dest_dir / member_path).resolve()
            if not target.is_relative_to(dest_dir):
                raise ValidationAppError(f"Unsafe path in archive: {member.filename}")

            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, open(target, "wb") as out:
                out.write(source.read())


def flatten_single_root(dest_dir: Path) -> None:
    """If extraction produced a single top-level directory, hoist its contents up.

    Zip archives exported from GitHub ("Download ZIP") wrap everything in a
    `<repo>-<branch>/` directory; without this the imported project's root
    would sit one level too deep.
    """
    entries = list(dest_dir.iterdir())
    if len(entries) != 1 or not entries[0].is_dir():
        return

    nested = entries[0]
    for child in nested.iterdir():
        child.rename(dest_dir / child.name)
    nested.rmdir()
