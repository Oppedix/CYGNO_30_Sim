#!/usr/bin/env python3
"""Verified uncompressed external campaign tar; safe, no-overwrite restoration."""
from pathlib import Path
import os
import sys
import tarfile
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from study import runtime as rt
from study.source_matrix import require
from study.archive import checksums, archive_inventory, extract
from external.study.simulate import check_campaign


def pack(source, output):
    source, output = source.resolve(), output.resolve()
    require(not output.exists() and not output.is_relative_to(source), 'Archive must be new and outside the campaign')
    check_campaign(source)
    # The packer operates on a worker-owned completed output, never a joined input.
    index = checksums(source); rt.save(source/'SHA256SUMS.json', index)
    temporary = output.with_name(output.name+'.partial')
    with temporary.open('xb') as stream, tarfile.open(fileobj=stream, mode='w') as tar:
        for name in ['SHA256SUMS.json', *index]: tar.add(source/name, arcname='campaign/'+name, recursive=False)
    require(archive_inventory(temporary) == index and checksums(source) == index, 'Campaign changed during packaging')
    os.link(temporary, output); temporary.unlink()
    with output.with_name(output.name+'.sha256').open('x') as f: f.write(rt.digest(output)+'  '+output.name+'\n')


def restore(archive, output):
    archive, output = archive.resolve(), output.resolve()
    require(not output.exists(), 'Refusing to overwrite a campaign')
    checksum = archive.with_name(archive.name+'.sha256').read_text().strip().split()
    require(checksum == [rt.digest(archive), archive.name], 'Transfer archive SHA256 mismatch')
    # Validate the complete stream before extraction; study.archive rejects traversal and links.
    archive_inventory(archive)
    staging = output.with_name(output.name+'.partial'); staging.mkdir(parents=True, exist_ok=False)
    root = extract(archive, staging)
    check_campaign(root)
    root.rename(output); staging.rmdir()
    print('Restored complete campaign: '+str(output))


if __name__ == '__main__':
    try:
        require(len(sys.argv) == 4 and sys.argv[1] in ('pack', 'restore'), 'Usage: campaign_transfer.py pack|restore INPUT NEW_OUTPUT')
        (pack if sys.argv[1] == 'pack' else restore)(Path(sys.argv[2]), Path(sys.argv[3]))
    except (ValueError, OSError, KeyError, tarfile.TarError) as e:
        print('Campaign transfer: '+str(e), file=sys.stderr); sys.exit(1)
