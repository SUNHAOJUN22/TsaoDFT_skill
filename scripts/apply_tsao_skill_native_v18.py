from __future__ import annotations

import base64
import importlib.util
import io
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / ".tsao-skill-native-v18"


def safe_members(archive: tarfile.TarFile) -> list[tarfile.TarInfo]:
    members: list[tarfile.TarInfo] = []
    for member in archive.getmembers():
        path = Path(member.name)
        if member.issym() or member.islnk():
            raise RuntimeError(f"links are not allowed in V18 payload: {member.name}")
        if path.is_absolute() or ".." in path.parts:
            raise RuntimeError(f"unsafe V18 payload path: {member.name}")
        members.append(member)
    return members


def load_transform(path: Path, index: int):
    name = f"_tsao_v18_transform_{index}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load transform: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    apply = getattr(module, "apply", None)
    if not callable(apply):
        raise RuntimeError(f"transform has no callable apply(root): {path}")
    return apply


def main() -> int:
    parts = sorted(STAGE.glob("payload.b64.part-*"))
    if not parts:
        raise RuntimeError("V18 payload parts are missing")
    encoded = "".join(path.read_text(encoding="ascii") for path in parts)
    archive_bytes = base64.b64decode(encoded, validate=True)
    copied = 0
    transformed = 0
    with tempfile.TemporaryDirectory(prefix="tsao-v18-") as temp_dir:
        temp = Path(temp_dir)
        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as archive:
            archive.extractall(temp, members=safe_members(archive))
        payload = temp / "payload"
        files = payload / "files"
        transforms = payload / "transforms"
        if files.is_dir():
            for source in sorted(files.rglob("*")):
                if not source.is_file():
                    continue
                relative = source.relative_to(files)
                target = ROOT / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                copied += 1
        if transforms.is_dir():
            for index, transform in enumerate(sorted(transforms.glob("*.py")), start=1):
                result = load_transform(transform, index)(ROOT)
                if result is not None and not isinstance(result, list):
                    raise RuntimeError(f"unexpected transform result from {transform.name}: {type(result)!r}")
                transformed += 1
    print({"copied_files": copied, "transforms_applied": transformed})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
