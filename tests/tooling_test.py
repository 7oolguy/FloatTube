import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

class ReleaseVersionTests(unittest.TestCase):
    def test_semver_rules(self):
        next_version = module('version').next_version
        self.assertEqual(next_version('v1.2.3', ['fix: corrige alinhamento']), '1.2.4')
        self.assertEqual(next_version('v1.2.3', ['feat: adiciona atualização']), '1.3.0')
        self.assertEqual(next_version('v1.2.3', ['feat!: altera requisito']), '2.0.0')
        self.assertEqual(next_version('v1.2.3', ['chore: organiza arquivos']), '1.2.3')
        self.assertEqual(next_version('', ['feat: cria extensão']), '0.1.0')

class UpdateSecurityTests(unittest.TestCase):
    def test_archive_rejects_traversal_and_other_roots(self):
        updater = module('update')
        for name in ['../escape', '/absolute', 'Other.app/file', 'FloatTube.app/../escape', 'FloatTube.app\\evil']:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'update.zip'
                with zipfile.ZipFile(path, 'w') as archive: archive.writestr(name, 'x')
                with self.assertRaises(ValueError): updater.validate_archive(path)

    def test_archive_rejects_symlink(self):
        updater = module('update')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'update.zip'
            entry = zipfile.ZipInfo('FloatTube.app/link')
            entry.external_attr = 0o120777 << 16
            with zipfile.ZipFile(path, 'w') as archive: archive.writestr(entry, '/outside')
            with self.assertRaises(ValueError): updater.validate_archive(path)

    def test_archive_accepts_app_and_versions_are_numeric(self):
        updater = module('update')
        self.assertGreater(updater.version('1.10.0'), updater.version('1.9.0'))
        with self.assertRaises(ValueError): updater.version('1.2.3-beta')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'update.zip'
            with zipfile.ZipFile(path, 'w') as archive: archive.writestr('FloatTube.app/Contents/Info.plist', 'x')
            updater.validate_archive(path)

if __name__ == '__main__': unittest.main()
