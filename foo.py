#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-

from icecream import ic

d = {1:'1'*30, 2:'2'*30, 3:'3'*30}

ic(d)

ic.configureOutput(argToStringFunction=lambda _: str(_))
ic(d)
