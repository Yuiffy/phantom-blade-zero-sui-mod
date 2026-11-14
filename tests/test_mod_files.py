"""Exercise installer boundaries in a disposable fake Steam library."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('mod_files', Path(__file__).parents[1] / 'scripts/mod_files.py')
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.game = root / 'steamapps/common/PBZ'
        (self.game / 'platform/steam').mkdir(parents=True)
        (self.game / 'platform/steam/PBZ.exe').write_bytes(b'fixture, never executed')
        (self.game / 'ProjectPBZ/Content/Paks').mkdir(parents=True)
        self.app = root / 'steamapps/appmanifest_4115450.acf'
        self.app.write_text('"buildid" "26367565"')
        self.target = self.game / 'ProjectPBZ/Content/Paks/~mods'
        package = root / 'package'
        (package / 'mod').mkdir(parents=True)
        self.manifest = package / 'manifest.json'
        self.receipt = package / 'manifest.receipt.json'
        self.data = {'variant': 'fixture', 'game_build': '26367565', 'steam_app_id': '4115450', 'files': []}
        for ext in ['.pak', '.utoc', '.ucas']:
            name = 'z_Sui_Fixture_P' + ext
            data = ('unique fixture ' + ext).encode()
            (package / 'mod' / name).write_bytes(data)
            self.data['files'].append({'name': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        self.save_manifest()

    def save_manifest(self):
        self.manifest.write_text(json.dumps(self.data), encoding='utf-8')

    def install(self, apply=True):
        with patch.object(mod, 'stopped'):
            return mod.install(self.manifest, self.game, self.receipt, apply)

    def test_dry_run_writes_nothing(self):
        self.install(False)
        self.assertFalse(self.target.exists())
        self.assertFalse(self.receipt.exists())

    def test_install_remove_preserves_unrelated_files_and_supports_game_update(self):
        self.target.mkdir()
        unrelated = self.target / 'unrelated.txt'
        unrelated.write_bytes(b'keep')
        self.install()
        self.assertTrue(self.receipt.is_file())
        self.app.write_text('"buildid" "99999999"')
        with patch.object(mod, 'stopped'):
            mod.uninstall(self.manifest, self.game, self.receipt, True)
        self.assertEqual(unrelated.read_bytes(), b'keep')
        self.assertEqual([p.name for p in self.target.iterdir()], ['unrelated.txt'])

    def test_modified_destination_blocks_entire_uninstall(self):
        self.install()
        (self.target / self.data['files'][0]['name']).write_bytes(b'changed')
        with patch.object(mod, 'stopped'), self.assertRaises(ValueError):
            mod.uninstall(self.manifest, self.game, self.receipt, True)
        self.assertEqual(len(list(self.target.iterdir())), 3)

    def test_running_game_refuses_before_write(self):
        with patch.object(mod, 'stopped', side_effect=ValueError('PBZ running')):
            with self.assertRaises(ValueError):
                mod.install(self.manifest, self.game, self.receipt, True)
        self.assertFalse(self.target.exists())

    def test_wrong_build_refuses_before_write(self):
        self.app.write_text('"buildid" "99999999"')
        with self.assertRaises(ValueError):
            self.install()
        self.assertFalse(self.target.exists())

    def test_path_traversal_manifest_is_rejected(self):
        self.data['files'][0]['name'] = '../z_Sui_Fixture_P.pak'
        self.save_manifest()
        with self.assertRaises(ValueError):
            mod.verify(self.manifest)

    def test_corrupt_source_refuses_before_write(self):
        (self.manifest.parent / 'mod' / self.data['files'][0]['name']).write_bytes(b'bad')
        with self.assertRaises(ValueError):
            self.install()
        self.assertFalse(self.target.exists())

    def test_mid_install_failure_cleans_up_created_files(self):
        with patch.object(mod, 'stopped', side_effect=[None, None, ValueError('PBZ started')]):
            with self.assertRaises(ValueError):
                mod.install(self.manifest, self.game, self.receipt, True)
        self.assertEqual(list(self.target.iterdir()), [])
        self.assertFalse(self.receipt.exists())


if __name__ == '__main__':
    unittest.main()
