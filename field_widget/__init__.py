import os
import logging
from lxml import etree

from odoo import tools
from odoo.tools import view_validation

old_relaxng = view_validation.relaxng
_cache = {}
_logger = logging.getLogger(__name__)


def new_relaxng(view_type):
    """ Return a validator for the given view type, or None. """
    if view_type != 'tree':
        return old_relaxng(view_type)
    if view_type not in _cache:
        with tools.file_open(os.path.join('field_widget', 'rng', 'tree_view.rng')) as frng:
            try:
                relaxng_doc = etree.parse(frng)
                _cache[view_type] = etree.RelaxNG(relaxng_doc)
            except Exception:
                _logger.exception('Failed to load RelaxNG XML schema for views validation')
                _cache[view_type] = None
    return _cache[view_type]

view_validation.relaxng = new_relaxng
