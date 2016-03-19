#!/usr/bin/env python3
# coding=UTF-8

from __future__ import unicode_literals

beta = u')bgdhwzx+yklmns(pcqr#&$t'
hebr = u'אבגדהוזחטיכלמנסעפצקרששׂשׁת'
sub_d = dict(zip(beta, hebr))
beta_vow = u'a f i e " o u w. : ow :a :f :e - .'.split()
hebr_vow = u'םַ םָ םִ םֶ םֵ םֹ םֻ וּ  םְ וֹ  םֲ  םֳ  םֱ  ־ םּ'.replace(u'ם', u'').split()
pass_through = set(' \t\n־')
sub_d.update(dict(zip(beta_vow, hebr_vow)))

medial = 'כמנפצ'
final  = 'ךםןףץ'
final_d = dict(zip(medial, final))
medial_s = set(medial)


def _finalize(decoded):
    if decoded[-1] in medial_s:
        decoded[-1] = final_d[decoded[-1]]


def decode(betacode):
    betacode = betacode.lower()
    decoded = []
    for char in betacode:
        try:
            decoded.append(sub_d[char])
        except KeyError:
            if char in pass_through:
                _finalize(decoded)
                decoded.append(char)
            elif char !='\\':
                raise
    _finalize(decoded)
    return ''.join(decoded)


def main():
    import sys
    import unicodedata as ud
    betacode = sys.argv[1]

    fixed = decode(betacode)
    fixed = ud.normalize('NFC', fixed)
    print(fixed)
