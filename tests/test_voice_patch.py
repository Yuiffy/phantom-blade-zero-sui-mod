import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts/voice_patch'))
from generate import rebuild, validate, local_file, STEP
from iostore import RangeReader, FormatError
from make_recipe import Payload, same_offset_delta


def sha(data):
    return hashlib.sha256(data).hexdigest()


class FakeReader:
    def __init__(self, data):
        self.data = data

    def chunk(self, cid):
        return 0, len(self.data)

    def read(self, cid, offset, size):
        return self.data[offset:offset+size]


class VoicePatchTests(unittest.TestCase):
    def fixture(self, root):
        bundle = root/'bundle'; bundle.mkdir()
        old, new = b'original bank data', b'original BANK data'
        payload = Payload()
        ops = same_offset_delta(old, new, 0, payload)
        recipe = {'format':'pbz-voice-recipe-1', 'payload':{'name':'payload.bin',
                  'bytes':len(payload.data), 'sha256':sha(payload.data)},
                  'chunks':[{'bytes':len(new), 'sha256':sha(new), 'source':{
                      'id':'01'*12, 'bytes':len(old), 'sha256':sha(old)}, 'ops':ops}],
                  'outputs':[]}
        for ext, data in [('pak',b'pak'),('utoc',b'toc'),('ucas',new)]:
            item = {'name':'z_Sui_Test_P.'+ext,'bytes':len(data),'sha256':sha(data)}
            if ext != 'ucas':
                item['template'] = ext+'.bin'; (bundle/item['template']).write_bytes(data)
            recipe['outputs'].append(item)
        (bundle/'payload.bin').write_bytes(payload.data)
        (bundle/'recipe.json').write_text(json.dumps(recipe), encoding='utf-8')
        return bundle, recipe, old, new

    def test_reconstruction(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); bundle, _, old, new = self.fixture(root)
            rebuild(bundle, root/'out', FakeReader(old), lambda:None)
            self.assertEqual((root/'out/z_Sui_Test_P.ucas').read_bytes(), new)
            self.assertEqual(len(list((root/'out').iterdir())), 3)

    def test_wrong_source_cleans_partial_output(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); bundle, _, old, _ = self.fixture(root)
            with self.assertRaisesRegex(FormatError, 'Source chunk integrity'):
                rebuild(bundle, root/'out', FakeReader(old.upper()), lambda:None)
            self.assertFalse((root/'out').exists())
            self.assertEqual(list(root.glob('.pbz-voice-building-*')), [])

    def test_payload_corruption_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); bundle, _, old, _ = self.fixture(root)
            (bundle/'payload.bin').write_bytes(b'bad')
            with self.assertRaisesRegex(FormatError, 'payload integrity'):
                rebuild(bundle, root/'out', FakeReader(old), lambda:None)
            self.assertFalse((root/'out').exists())

    def test_output_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); bundle, _, old, _ = self.fixture(root)
            (root/'out').mkdir(); (root/'out/sentinel').write_bytes(b'keep')
            with self.assertRaisesRegex(FormatError, 'already exists'):
                rebuild(bundle, root/'out', FakeReader(old), lambda:None)
            self.assertEqual((root/'out/sentinel').read_bytes(), b'keep')

    def test_refuses_running_game(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); bundle, _, old, _ = self.fixture(root)
            def running():
                raise FormatError('Close Phantom Blade Zero')
            with self.assertRaisesRegex(FormatError, 'Close Phantom'):
                rebuild(bundle, root/'out', FakeReader(old), running)
            self.assertFalse((root/'out').exists())

    def test_interrupt_after_output_created_cleans(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); bundle, _, old, _ = self.fixture(root)
            count = [0]
            def stop():
                count[0] += 1
                if count[0] == 3:
                    raise FormatError('Game started during reconstruction')
            with self.assertRaisesRegex(FormatError, 'Game started'):
                rebuild(bundle, root/'out', FakeReader(old), stop)
            self.assertFalse((root/'out').exists())
            self.assertEqual(list(root.glob('.pbz-voice-building-*')), [])

    def test_bounds_and_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); _, recipe, _, _ = self.fixture(root)
            for name in ['../escape','C:/outside','..\\outside']:
                with self.assertRaises(FormatError):
                    local_file(root, name)
            for op in [['copy',0,10000],['add',-1,2],['zero',-2],['exec','x']]:
                recipe['chunks'][0]['ops'] = [op]
                with self.assertRaises(FormatError):
                    validate(recipe, 100)

    def test_final_hash_failure_cleans(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); bundle, recipe, old, _ = self.fixture(root)
            recipe['outputs'][2]['sha256'] = '0'*64
            (bundle/'recipe.json').write_text(json.dumps(recipe), encoding='utf-8')
            with self.assertRaisesRegex(FormatError, 'Final output hash'):
                rebuild(bundle, root/'out', FakeReader(old), lambda:None)
            self.assertFalse((root/'out').exists())

    def test_large_bulk_prefix_hash_and_streaming(self):
        for corrupt in [False, True]:
            with self.subTest(corrupt=corrupt), tempfile.TemporaryDirectory() as d:
                root = Path(d); bundle, recipe, _, _ = self.fixture(root)
                old = b'x'*(STEP+1)
                payload = (bundle/'payload.bin').read_bytes()
                new = old + payload
                recipe['chunks'] = [{'bytes':len(new), 'sha256':sha(new), 'source':{
                    'id':'01'*12,'bytes':len(old),'sha256':sha(old)},
                    'ops':[['copy',0,len(old)],['add',0,len(payload)]]}]
                recipe['outputs'][2].update(bytes=len(new), sha256=sha(new))
                (bundle/'recipe.json').write_text(json.dumps(recipe), encoding='utf-8')
                if corrupt:
                    with self.assertRaisesRegex(FormatError,'Source bulk integrity'):
                        rebuild(bundle,root/'out',FakeReader(old[:-1]+b'y'),lambda:None)
                    self.assertFalse((root/'out').exists())
                else:
                    rebuild(bundle,root/'out',FakeReader(old),lambda:None)
                    self.assertEqual((root/'out/z_Sui_Test_P.ucas').read_bytes(),new)


class IoStoreTests(unittest.TestCase):
    def fixture(self, root, encrypted=False):
        cid = 'a1'*12
        data = b'fake chunk bytes spanning two blocks'
        block_size = 32
        blocks = [data[:block_size], data[block_size:]]
        header = bytearray(144)
        header[:16] = b'-==--==--==--==-'
        header[16] = 8
        struct.pack_into('<9I', header, 20, 144, 1, 2, 12, 0, 32, block_size, 0, 1)
        header[80] = 2 if encrypted else 0
        struct.pack_into('<Q', header, 88, 1<<30)
        table = bytearray(); physical = bytearray(); key = bytes(range(32))
        for b in blocks:
            table.extend(struct.pack('<QI', len(physical) | (len(b)<<40), len(b)))
            if encrypted:
                from Crypto.Cipher import AES
                b = AES.new(key,AES.MODE_ECB).encrypt(b+bytes((-len(b))%16))
            physical.extend(b)
        toc = root/'fixture.utoc'
        toc.write_bytes(header+bytes.fromhex(cid)+bytes(5)+len(data).to_bytes(5,'big')+table)
        toc.with_suffix('.ucas').write_bytes(physical)
        return toc, cid, data, key

    def test_plain_and_encrypted_ranges(self):
        for encrypted in [False,True]:
            with self.subTest(encrypted=encrypted), tempfile.TemporaryDirectory() as d:
                toc, cid, data, key = self.fixture(Path(d), encrypted)
                with RangeReader(toc,key=key) as reader:
                    self.assertEqual(reader.read(cid,3,len(data)-5),data[3:-2])
                    self.assertEqual(reader.read(cid,0,len(data)),data)
                    with self.assertRaises(FormatError):
                        reader.read(cid,0,len(data)+1)

    def test_truncated_partition(self):
        with tempfile.TemporaryDirectory() as d:
            toc, cid, data, _ = self.fixture(Path(d))
            toc.with_suffix('.ucas').write_bytes(b'truncated')
            with RangeReader(toc) as reader, self.assertRaisesRegex(FormatError,'Truncated'):
                reader.read(cid,0,len(data))


if __name__ == '__main__':
    unittest.main()
