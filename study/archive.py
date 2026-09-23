"""Portable complete-campaign archives with strict regular-file extraction."""
import argparse
from contextlib import contextmanager
import os
import hashlib
import json
import time
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from study import runtime as rt
from study.campaign import inside, validate_campaign
from study.source_matrix import require

INDEX = 'SHA256SUMS.json'


def checksums(root):
    result = {}
    for path in sorted(root.rglob('*')):
        require(not path.is_symlink(), 'Campaign contains a symlink')
        if path.is_file() and path.relative_to(root).as_posix() not in (INDEX, '.runner.lock'):
            result[path.relative_to(root).as_posix()] = rt.digest(path)
    return result


def verify_checksums(root):
    expected = rt.read(root/INDEX)
    require(expected == checksums(root), 'Archive file inventory/checksum mismatch')


def package(root, destination=None):
    """Caller holds the campaign lock. Never publish a partial campaign archive."""
    root = root.resolve()
    validate_campaign(root)
    automatic_name = destination is None
    destination = destination or root.with_name(root.name+'.tar.gz')
    destination = destination.resolve()
    require(not destination.is_relative_to(root), 'Archive must be outside the campaign')
    inventory = checksums(root)
    rt.save(root/INDEX, inventory)
    if destination.exists():
        if archive_inventory(destination) == inventory:
            archive_checksum(destination)
            return destination
        require(automatic_name, 'Existing archive differs; choose a new --output archive name')
        destination = root.with_name(root.name+f'-{time.time_ns()}.tar.gz')
    descriptor, name = tempfile.mkstemp(prefix=destination.name+'.', suffix='.tmp', dir=destination.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, 'wb') as file:
            with tarfile.open(fileobj=file, mode='w:gz', compresslevel=1) as archive:
                for name in [INDEX, *inventory]:
                    archive.add(root/name, arcname='campaign/'+name, recursive=False)
        # Detect files changing during packaging before publication.
        require(inventory == checksums(root), 'Campaign changed while packaging')
        require(archive_inventory(temporary) == inventory, 'Archive verification failed')
        os.link(temporary, destination)  # fails rather than replacing an existing archive
        archive_checksum(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def archive_checksum(path):
    checksum = path.with_name(path.name+'.sha256')
    text = rt.digest(path)+'  '+path.name+'\n'
    if checksum.exists():
        require(checksum.read_text() == text, 'Existing archive SHA256 mismatch')
    else:
        checksum.write_text(text)


def archive_inventory(path):
    """Stream verification without creating a second uncompressed campaign copy."""
    observed, expected = {}, None
    with tarfile.open(path, 'r|*') as archive:
        for member in archive:
            require(member.isfile() and member.name.startswith('campaign/'), 'Invalid archive member')
            name = member.name.removeprefix('campaign/')
            inside(Path('/campaign'), name)
            require(name not in observed, 'Duplicate archive member')
            with archive.extractfile(member) as file:
                if name == INDEX:
                    require(expected is None and member.size < 100_000_000, 'Invalid checksum index')
                    expected = json.load(file)
                    observed[name] = None
                else:
                    checksum = hashlib.sha256()
                    for block in iter(lambda: file.read(1024*1024), b''):
                        checksum.update(block)
                    observed[name] = checksum.hexdigest()
    observed.pop(INDEX, None)
    require(expected is not None and expected == observed, 'Archive file inventory/checksum mismatch')
    return expected


def extract(archive_path, destination):
    """Reject links, devices, duplicate members and traversal before writing anything."""
    with tarfile.open(archive_path, 'r:*') as archive:
        members = archive.getmembers()
        seen = set()
        for member in members:
            require(member.isfile() and member.name != 'campaign/.runner.lock',
                    'Only packaged regular files are allowed in campaign archives')
            require(member.name not in seen, 'Duplicate archive member')
            seen.add(member.name)
            path = inside(destination, member.name)
            require(member.name.startswith('campaign/') and path != destination/'campaign', 'Invalid archive root')
        for member in members:
            path = inside(destination, member.name)
            path.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(member) as source, path.open('xb') as target:
                shutil.copyfileobj(source, target, length=1024*1024)
    root = destination/'campaign'
    verify_checksums(root)
    return root


@contextmanager
def open_campaign(path):
    path = Path(path).resolve()
    if path.is_dir():
        # A live campaign can have new resume probes since an earlier archive.
        # Its authoritative manifests are validated independently by the caller.
        yield path
    else:
        checksum = path.with_name(path.name+'.sha256')
        if checksum.exists():
            require(checksum.read_text().split()[0] == rt.digest(path), 'Archive SHA256 mismatch')
        with tempfile.TemporaryDirectory(prefix='cygno-campaign-') as directory:
            yield extract(path, Path(directory))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='Completed unpacked campaign')
    parser.add_argument('--output', type=Path, help='New .tar.gz path; default INPUT.tar.gz')
    args = parser.parse_args()
    try:
        with rt.locked(args.input.resolve()):
            print(package(args.input, args.output))
        return 0
    except (ValueError, OSError, KeyError, tarfile.TarError) as error:
        print(f'Archive: {error}', file=sys.stderr)
        return 1

if __name__ == '__main__': sys.exit(main())
