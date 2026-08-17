# -*- coding: utf-8 -*-
"""Simple native list row for Revival social records."""
from __future__ import absolute_import

from aoslib.scenes.main.listPanelItemBase import ListPanelItemBase


class SocialListItem(ListPanelItemBase):

    def initialize(self, name, uid, kind, record):
        ListPanelItemBase.initialize(self, name=name, uid=uid)
        self.kind = kind
        self.record = record
        self.center_text = False


__all__ = ["SocialListItem"]
