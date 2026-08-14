import sys
import unittest
from unittest import mock

import zc.buildout

from collective.recipe.plonesite import Recipe


def import_plonesite():
    """ `plonesite.py` is self contained, stub imports. """
    modules = [
        'AccessControl',
        'AccessControl.SecurityManagement',
        'Products',
        'Products.CMFPlone',
        'Products.CMFPlone.factory',
        'Testing',
        'Testing.makerequest',
        'transaction',
        'zExceptions',
        'zExceptions.unauthorized',
        'zope.component',
        'zope.component.hooks',
    ]
    stubs = {name: mock.MagicMock() for name in modules}
    with mock.patch.dict(sys.modules, stubs):
        from collective.recipe.plonesite import plonesite
    return plonesite


class FakeBuildout(dict):
    """ Make ``Recipe.__init__`` work."""

    _log_level = 20

    def __init__(self):
        super().__init__({
            'buildout': {
                'parts-directory': 'parts',
                'bin-directory': 'bin',
            },
            'instance': {'location': 'parts/instance'},
        })


class TestRecipe(unittest.TestCase):

    def _createArgs(self, **options):
        recipe = Recipe(
            buildout=FakeBuildout(), name='plonesite', options=options
        )
        return recipe.createArgs()

    def test_products_option_raises_user_error(self):
        options = {'products': 'MyProduct'}
        with self.assertRaises(zc.buildout.UserError) as cm:
            Recipe(buildout={}, name='plonesite', options=options)
        self.assertIn('products', str(cm.exception))

    def test_products_initial_option_raises_user_error(self):
        options = {'products-initial': 'MyProduct'}
        with self.assertRaises(zc.buildout.UserError) as cm:
            Recipe(buildout={}, name='plonesite', options=options)
        self.assertIn('products-initial', str(cm.exception))

    def test_distribution_is_passed_on(self):
        self.assertIn(
            '--distribution=none', self._createArgs(distribution='none')
        )

    def test_distribution_is_omitted_when_unset(self):
        # No option means the script keeps auto-detecting.
        self.assertNotIn('--distribution', self._createArgs())


class TestGetDistributionName(unittest.TestCase):

    def setUp(self):
        self.plonesite = import_plonesite()

    def distribution_name(self, has_classic, has_volto, override=''):
        with mock.patch.multiple(
            self.plonesite,
            HAS_CLASSIC=has_classic,
            HAS_VOLTO=has_volto,
        ):
            return self.plonesite.getDistributionName(override)

    def test_classic_wins(self):
        self.assertEqual(
            self.distribution_name(has_classic=True, has_volto=True),
            "classic",
        )

    def test_classic_only(self):
        self.assertEqual(
            self.distribution_name(has_classic=True, has_volto=False),
            "classic",
        )

    def test_volto_only(self):
        self.assertEqual(
            self.distribution_name(has_classic=False, has_volto=True),
            "volto",
        )

    def test_no_distribution_installed(self):
        # `plone.distribution` is a core add-on, not a dependency
        # the recipe must not assume it is around
        self.assertIsNone(
            self.distribution_name(has_classic=False, has_volto=False)
        )

    def test_override_none_beats_autodetection(self):
        # 'Plone' has both `plone.classicui` and `plone.volto`
        # policy packages that run their own profile need a
        # way to opt out of distributions entirely
        self.assertIsNone(
            self.distribution_name(
                has_classic=True, has_volto=True, override='none'
            )
        )

    def test_override_none_is_case_insensitive(self):
        self.assertIsNone(
            self.distribution_name(
                has_classic=True, has_volto=True, override='None'
            )
        )

    def test_override_selects_named_distribution(self):
        self.assertEqual(
            self.distribution_name(
                has_classic=True, has_volto=True, override='volto'
            ),
            'volto',
        )

    def test_override_allows_a_custom_distribution(self):
        self.assertEqual(
            self.distribution_name(
                has_classic=False, has_volto=False, override='unibonn'
            ),
            'unibonn',
        )

    def test_blank_override_falls_back_to_autodetection(self):
        self.assertEqual(
            self.distribution_name(
                has_classic=True, has_volto=False, override='  '
            ),
            'classic',
        )
