#-------------------------------------------------------------------------------
# Name:        data
# Purpose:
#
# Author:      Sergey Pikhovkin (s@pikhovkin.ru)
#
# Created:     03.02.2011
# Copyright:   (c) Sergey Pikhovkin 2011
# Licence:     MIT
#-------------------------------------------------------------------------------
#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json


class Dict2Object(object):
    def __init__(self, dict):
        self.__dict__ = dict


class JSON2Obj(Dict2Object):
    def __init__(self, page):
        super(JSON2Obj, self).__init__(json.loads(page))


def main():
    d = '{"aa":"bb", "cc":{"i": "ds"}, "gg": [34, 56]}'
    o = JSON2Obj(d)
    print o.aa

if __name__ == '__main__':
    main()
