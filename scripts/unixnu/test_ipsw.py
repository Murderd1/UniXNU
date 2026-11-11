"""Offline regressions for interrupted HTTP ranges and resumed IPSW members."""
import hashlib
import http.client
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unixnu.ipsw import Ipsw, RangeFile
from unixnu.util import Error


class InterruptedRanges(unittest.TestCase):
    def stream(self):
        stream = RangeFile.__new__(RangeFile)
        stream.url, stream.block, stream.size = 'https://example.invalid/input.ipsw', 8, 8
        stream.retries, stream.cache = 4, {}
        return stream

    def test_incomplete_response_is_retried_without_caching_truncated_bytes(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.side_effect = [http.client.IncompleteRead(b'bad', 5), b'complete']
        stream = self.stream()
        with patch('unixnu.ipsw.urllib.request.urlopen', return_value=response) as request, patch('unixnu.ipsw.time.sleep'):
            self.assertEqual(stream._block(0), b'complete')
        self.assertEqual(request.call_count, 2)
        self.assertEqual(stream.cache, {0: b'complete'})

    def test_persistent_truncation_stops_after_the_retry_limit(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.side_effect = http.client.IncompleteRead(b'bad', 5)
        stream = self.stream()
        with patch('unixnu.ipsw.urllib.request.urlopen', return_value=response) as request, patch('unixnu.ipsw.time.sleep'):
            with self.assertRaises(http.client.IncompleteRead):
                stream._block(0)
        self.assertEqual(request.call_count, 4)
        self.assertEqual(stream.cache, {})


class ResumeMembers(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.data = b'original encrypted system volume'
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_STORED) as package:
            package.writestr('system.dmg.aea', self.data)
        self.ipsw = Ipsw.__new__(Ipsw)
        self.ipsw.remote = False
        self.ipsw.zip = zipfile.ZipFile(archive)
        self.ipsw.config = {'sha256': {'system.dmg.aea': hashlib.sha256(self.data).hexdigest()}}
        self.ipsw.identity = {'Manifest': {'OS': {'Info': {'Path': 'system.dmg.aea'}}}}
        self.ipsw.cache = self.root
        self.partial = self.root / 'system.dmg.aea.partial'

    def tearDown(self):
        self.ipsw.zip.close()
        self.temp.cleanup()

    def test_saved_prefix_is_skipped_and_the_whole_member_is_hashed(self):
        self.partial.write_bytes(self.data[:9])
        opened = self.ipsw.zip.open
        seeks = []
        def track(*args, **kwargs):
            source = opened(*args, **kwargs)
            seek = source.seek
            source.seek = lambda offset: (seeks.append(offset), seek(offset))[1]
            return source
        with patch.object(self.ipsw.zip, 'open', side_effect=track):
            output = self.ipsw.extract('OS')
        self.assertEqual(seeks, [9])
        self.assertEqual(output.read_bytes(), self.data)
        self.assertEqual(json.loads(output.with_suffix('.aea.json').read_text())['sha256'], hashlib.sha256(self.data).hexdigest())
        self.assertFalse(self.partial.exists())

    def test_corrupt_prefix_is_rejected_even_without_a_sha256_pin(self):
        self.ipsw.config = {}
        self.partial.write_bytes(b'corrupt!!')
        with self.assertRaisesRegex(Error, 'member CRC'):
            self.ipsw.extract('OS')
        self.assertFalse((self.root / 'system.dmg.aea').exists())
        self.assertTrue(self.partial.exists())

    def test_complete_partial_is_verified_before_publication(self):
        self.partial.write_bytes(self.data)
        self.assertEqual(self.ipsw.extract('OS').read_bytes(), self.data)


if __name__ == '__main__':
    unittest.main()
