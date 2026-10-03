"""Host-only guards for the downloadable bundle boundary."""
import hashlib
import io
from pathlib import Path
import struct
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import build

class BoundaryTests(unittest.TestCase):
    def test_stripped_foreign_and_truncated_elf_rejected(self):
        elf = bytearray(128)
        elf[:6] = b'\x7fELF\x02\x01'
        struct.pack_into('<H', elf, 18, 62)
        struct.pack_into('<Q', elf, 40, 64)
        struct.pack_into('<HH', elf, 58, 64, 1)
        build.check_elf(elf)
        for offset, fmt, value in [(18, '<H', 183), (40, '<Q', 0), (60, '<H', 2)]:
            bad = bytearray(elf)
            struct.pack_into(fmt, bad, offset, value)
            with self.assertRaises(ValueError):
                build.check_elf(bad)

    def test_digest_mismatch_is_fatal(self):
        with patch('urllib.request.urlopen', return_value=io.BytesIO(b'changed')):
            with self.assertRaisesRegex(ValueError, 'SHA-256'):
                build.download({'url': 'https://github.com/example/file',
                                'sha256': hashlib.sha256(b'original').hexdigest()})

    def test_archive_traversal_and_symlinks_rejected(self):
        for name, link in [('root/../../escape', False), ('root/link', True)]:
            stream = io.BytesIO()
            with tarfile.open(fileobj=stream, mode='w:gz') as archive:
                entry = tarfile.TarInfo(name)
                if link:
                    entry.type = tarfile.SYMTYPE
                    entry.linkname = '/etc/passwd'
                archive.addfile(entry)
            with tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(ValueError):
                    build.extract(stream.getvalue(), Path(directory), 'root')

if __name__ == '__main__':
    unittest.main()
