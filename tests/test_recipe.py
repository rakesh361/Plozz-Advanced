import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from check import ASSETS, already_published, marker, select_release
from materialize import installation_build


class RecipeTests(unittest.TestCase):
    def test_numbered_prereleases_and_numeric_hotfix_order(self):
        r = [{'tag_name': t, 'draft': False, 'prerelease': True}
             for t in ['release/069.9', 'release/069.10']]
        self.assertEqual(select_release(r)['tag_name'], 'release/069.10')

    def test_drafts_and_unrelated_tags_do_not_become_updates(self):
        r = [{'tag_name': 'release/999', 'draft': True},
             {'tag_name': 'experiment/999', 'draft': False},
             {'tag_name': 'release/070', 'draft': False}]
        self.assertEqual(select_release(r)['tag_name'], 'release/070')

    def test_missing_release_fails_closed(self):
        with self.assertRaises(ValueError): select_release([])

    def published(self):
        return [{'draft': False, 'body': marker('a'*40, 'b'*40),
                 'assets': [{'name': a} for a in ASSETS]}]

    def test_unchanged_release_and_recipe_skip_mac_build(self):
        self.assertTrue(already_published(self.published(), 'a'*40, 'b'*40))

    def test_new_source_or_recipe_requires_build(self):
        self.assertFalse(already_published(self.published(), 'c'*40, 'b'*40))
        self.assertFalse(already_published(self.published(), 'a'*40, 'c'*40))

    def test_partial_or_draft_publication_retries(self):
        r = self.published(); r[0]['assets'].pop()
        self.assertFalse(already_published(r, 'a'*40, 'b'*40))
        r = self.published(); r[0]['draft'] = True
        self.assertFalse(already_published(r, 'a'*40, 'b'*40))

    def test_new_numbering_updates_existing_installed_build(self):
        self.assertEqual(installation_build('1', '1'), '6001.1')
        self.assertGreater(tuple(map(int, installation_build('1','1').split('.'))), (5698,1))

    def test_invalid_installation_numbers_stop_release(self):
        for run, attempt in [('0','1'), ('4000','1'), ('1','0'), ('1','100')]:
            with self.assertRaises(ValueError): installation_build(run, attempt)
