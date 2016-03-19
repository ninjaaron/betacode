# coding=UTF-8
"""\
Convert Greek Betacode to Unicode. Whooo!

This module was hacked up based on the awesome Perl module, Encode::Betacode by
dgkontopoulos with some inspiration beta2unicode.py by James Tauber.

functions:

    betacode.decode(<betacode string>)

    - based on the the decode() function of the perl module. Uses simple string
      matching and a little regex to substitute every possible betacode
      combination. Ideal for doing longer text in one shot.

    betacode.trie_decode(<betacode string>)

    - This also turns betacode into Greek, but it is optimized for iterating on
      a lot of short strings, especially single words. For this use, it is
      about 16x faster than the standard decoded() because it uses prefix tree
      lookups for strings contained in the word instead of doing the "brute
      force" method of iterating on every possible substitution.

constants:

    betacode.subl [list]

    - a list of all betacode substitutions where each item is another list with
      the betacode representation at [0] and the (unescaped) unicode at [1].
      used by decode() to determine substitutions. A few of the items are
      regex for getting final sigma in the right place. Items have regex at
      [0], unicode at [1], and the number 0 at [2] (as an easy way to test if
      it should use regex or standard string substitution). This is easily
      converted into a dictionary with a comprehension, if you need that kind
      of thing. i.e. {i[0]: i[1] for i in betacode.subl}

    There is also a prefix tree, betacode.sub_tree, and some internal functions
    you could use with it, like betacode.climb() (for searching the tree). It's
    not really intended for external use, but feel free to poke around.
"""
from __future__ import unicode_literals

subl = [
    # Uppercase accents and diacritics
    ("*a&",   "Ᾱ"), ("*a'",   "Ᾰ"), ("*)/a|", "ᾌ"), ("*(/a|", "ᾍ"),
    ("*)=a|", "ᾎ"), ("*(=a|", "ᾏ"), ("*(\\a", "Ἃ"), ("*)/a",  "Ἄ"),
    ("*(/a",  "Ἅ"), ("*)=a",  "Ἆ"), ("*(=a",  "Ἇ"), ("*)a|",  "ᾈ"),
    ("*(a|",  "ᾉ"), ("*)a",   "Ἁ"), ("*(a",   "Ἁ"), ("*\\a",  "Ὰ"),
    ("*/a",   "Ά"), ("*a|",   "ᾼ"), ("*)\\a", "Ἂ"), ("*)\\e", "Ἒ"),
    ("*(\\e", "Ἓ"), ("*)/e",  "Ἔ"), ("*(/e",  "Ἕ"), ("*)e",   "Ἐ"),
    ("*(e",   "Ἑ"), ("*\\e",  "Ὲ"), ("*/e",   "Έ"), ("*)/h|", "ᾜ"),
    ("*(/h|", "ᾝ"), ("*)=h|", "ᾞ"), ("*(=h|", "ᾟ"), ("*)\\h", "Ἢ"),
    ("*(\\h", "Ἣ"), ("*)/h",  "Ἤ"), ("*(/h",  "Ἥ"), ("*)=h",  "Ἦ"),
    ("*(=h",  "Ἧ"), ("*)h|",  "ᾘ"), ("*(h|",  "ᾙ"), ("*)h",   "Ἠ"),
    ("*(h",   "Ἡ"), ("*\\h",  "Ὴ"), ("*/h",   "Ή"), ("*h|",   "ῌ"),
    ("*i&",   "Ῑ"), ("*i'",   "Ῐ"), ("*+i",   "Ϊ"), ("*)\\i", "Ἲ"),
    ("*(\\i", "Ἳ"), ("*)/i",  "Ἴ"), ("*(/i",  "Ἵ"), ("*)=i",  "Ἶ"),
    ("*(=i",  "Ἷ"), ("*)i",   "Ἰ"), ("*(i",   "Ἱ"), ("*\\i",  "Ὶ"),
    ("*/i",   "Ί"), ("*)\\o", "Ὂ"), ("*(\\o", "Ὃ"), ("*)/o",  "Ὄ"),
    ("*(/o",  "Ὅ"), ("*)=o",  "Ὄ"), ("*(=o",  "Ὅ"), ("*)o",   "Ὀ"),
    ("*(o",   "Ὁ"), ("*\\o",  "Ὸ"), ("*/o",   "Ό"), ("*)r",   "Ρ"),
    ("*(r",   "Ῥ"), ("*u&",   "Ῡ"), ("*u'",   "Ῠ"), ("*+u",   "Ϋ"),
    ("*(\\u", "Ὓ"), ("*(/u",  "Ὕ"), ("*(=u",  "Ὗ"), ("*(u",   "Ὑ"),
    ("*\\u",  "Ὺ"), ("*/u",   "Ύ"), ("*)/w|", "ᾬ"), ("*(/w|", "ᾭ"),
    ("*)=w|", "ᾮ"), ("*(=w|", "ᾯ"), ("*)\\w", "Ὢ"), ("*(\\w", "Ὣ"),
    ("*)/w",  "Ὤ"), ("*(/w",  "Ὥ"), ("*)=w",  "Ὦ"), ("*(=w",  "Ὧ"),
    ("*)w|",  "ᾨ"), ("*(w|",  "ᾩ"), ("*)w",   "Ὠ"), ("*(w",   "Ὡ"),
    ("*\\w",  "Ὼ"), ("*/w",   "Ώ"), ("*w|",   "ῼ"),
    # Duplicates, because some interpretations of betacode are different
    ("*a)/|", "ᾌ"), ("*a(/|", "ᾍ"), ("*a)=|", "ᾎ"), ("*a(=|", "ᾏ"),
    ("*a(\\", "Ἃ"), ("*a)/",  "Ἄ"), ("*a(/",  "Ἅ"), ("*a)=",  "Ἆ"),
    ("*a(=",  "Ἇ"), ("*a)|",  "ᾈ"), ("*a(|",  "ᾉ"), ("*a)",   "Ἁ"),
    ("*a(",   "Ἁ"), ("*a\\",  "Ὰ"), ("*a/",   "Ά"), ("*a|",   "ᾼ"),
    ("*a)\\", "Ἂ"), ("*e)\\", "Ἒ"), ("*e(\\", "Ἓ"), ("*e)/",  "Ἔ"),
    ("*e(/",  "Ἕ"), ("*e)",   "Ἐ"), ("*e(",   "Ἑ"), ("*e\\",  "Ὲ"),
    ("*e/",   "Έ"), ("*h)/|", "ᾜ"), ("*h(/|", "ᾝ"), ("*h)=|", "ᾞ"),
    ("*h(=|", "ᾟ"), ("*h)\\", "Ἢ"), ("*h(\\", "Ἣ"), ("*h)/",  "Ἤ"),
    ("*h(/",  "Ἥ"), ("*h)=",  "Ἦ"), ("*h(=",  "Ἧ"), ("*h)|",  "ᾘ"),
    ("*h(|",  "ᾙ"), ("*h)",   "Ἠ"), ("*h(",   "Ἡ"), ("*h\\",  "Ὴ"),
    ("*h/",   "Ή"), ("*h|",   "ῌ"), ("*i+",   "Ϊ"), ("*i)\\", "Ἲ"),
    ("*i(\\", "Ἳ"), ("*i)/",  "Ἴ"), ("*i(/",  "Ἵ"), ("*i)=",  "Ἶ"),
    ("*i(=",  "Ἷ"), ("*i)",   "Ἰ"), ("*i(",   "Ἱ"), ("*i\\",  "Ὶ"),
    ("*i/",   "Ί"), ("*o)\\", "Ὂ"), ("*o(\\", "Ὃ"), ("*o)/",  "Ὄ"),
    ("*o(/",  "Ὅ"), ("*o)=",  "Ὄ"), ("*o(=",  "Ὅ"), ("*o)",   "Ὀ"),
    ("*o(",   "Ὁ"), ("*o\\",  "Ὸ"), ("*o/",   "Ό"), ("*r)",   "Ρ"),
    ("*r(",   "Ῥ"), ("*u+",   "Ϋ"), ("*u(\\", "Ὓ"), ("*u(/",  "Ὕ"),
    ("*u(=",  "Ὗ"), ("*u(",   "Ὑ"), ("*u\\",  "Ὺ"), ("*u/",   "Ύ"),
    ("*w)/|", "ᾬ"), ("*w(/|", "ᾭ"), ("*w)=|", "ᾮ"), ("*w(=|", "ᾯ"),
    ("*w)\\", "Ὢ"), ("*w(\\", "Ὣ"), ("*w)/",  "Ὤ"), ("*w(/",  "Ὥ"),
    ("*w)=",  "Ὦ"), ("*w(=",  "Ὧ"), ("*w)|",  "ᾨ"), ("*w(|",  "ᾩ"),
    ("*w)",   "Ὠ"), ("*w(",   "Ὡ"), ("*w\\",  "Ὼ"), ("*w/",   "Ώ"),
    ("*w|",   "ῼ"),
    # Lowercase accents and diacritics
    ("a&",   "ᾱ"), ("a'",   "ᾰ"), ("a)/|", "ᾄ"), ("a(/|", "ᾅ"), ("a)=|", "ᾆ"),
    ("a(=|", "ᾇ"), ("a)|",  "ᾀ"), ("a(|",  "ᾁ"), ("a/|",  "ᾴ"), ("a=|",  "ᾷ"),
    ("a)\\", "ἂ"), ("a(\\", "ἃ"), ("a)/",  "ἄ"), ("a(/",  "ἅ"), ("a)=",  "ἆ"),
    ("a(=",  "ἇ"), ("a)",   "ἀ"), ("a(",   "ἁ"), ("a\\",  "ὰ"), ("a/",   "ά"),
    ("a=",   "ᾶ"), ("a|",   "ᾳ"), ("a+",   "α"), ("e)\\", "ἒ"), ("e(\\", "ἓ"),
    ("e)/",  "ἔ"), ("e(/",  "ἕ"), ("e)",   "ἐ"), ("e(",   "ἑ"), ("e\\",  "ὲ"),
    ("e/",   "έ"), ("h)/|", "ᾔ"), ("h(/|", "ᾕ"), ("h)=|", "ᾖ"), ("h(=|", "ᾗ"),
    ("h)|",  "ᾐ"), ("h(|",  "ᾑ"), ("h/|",  "ῄ"), ("h=|",  "ῇ"), ("h)\\", "ἢ"),
    ("h(\\", "ἣ"), ("h)/",  "ἤ"), ("h(/",  "ἥ"), ("h)=",  "ἦ"), ("h(=",  "ἧ"),
    ("h)",   "ἠ"), ("h(",   "ἡ"), ("h\\",  "ὴ"), ("h/",   "ή"), ("h=",   "ῆ"),
    ("h|",   "ῃ"), ("i&",   "ῑ"), ("i'",   "ῐ"), ("i+\\", "ῒ"), ("i\\+", "ῒ"),
    ("i+/",  "ΐ"), ("i/+",  "ΐ"), ("i+=",  "ῗ"), ("i=+",  "ῗ"), ("i+",   "ϊ"),
    ("i)\\", "ἲ"), ("i(\\", "ἳ"), ("i)/",  "ἴ"), ("i(/",  "ἵ"), ("i)=",  "ἶ"),
    ("i(=",  "ἷ"), ("i)",   "ἰ"), ("i(",   "ἱ"), ("i\\",  "ὶ"), ("i/",   "ί"),
    ("i=",   "ῖ"), ("o)\\", "ὂ"), ("o(\\", "ὃ"), ("o)/",  "ὄ"), ("o(/",  "ὅ"),
    ("o)",   "ὀ"), ("o(",   "ὁ"), ("o\\",  "ὸ"), ("o/",   "ό"), ("r)",   "ῤ"),
    ("r(",   "ῤ"), ("u&",   "ῡ"), ("u'",   "ῠ"), ("u+\\", "ῢ"), ("u\\+", "ῢ"),
    ("u+/",  "ΰ"), ("u/+",  "ΰ"), ("u+=",  "ῧ"), ("u=+",  "ῧ"), ("u+",   "ϋ"),
    ("u)\\", "ὒ"), ("u(\\", "ὓ"), ("u)/",  "ὔ"), ("u(/",  "ὕ"), ("u)=",  "ὖ"),
    ("u(=",  "ὗ"), ("u)",   "ὐ"), ("u(",   "ὑ"), ("u\\",  "ὺ"), ("u/",   "ύ"),
    ("u=",   "ῦ"), ("w)/|", "ᾤ"), ("w(/|", "ᾥ"), ("w)=|", "ᾦ"), ("w(=|", "ᾧ"),
    ("w)|",  "ᾠ"), ("w(|",  "ᾡ"), ("w/|",  "ῴ"), ("w=|",  "ῷ"), ("w)\\", "ὢ"),
    ("w(\\", "ὣ"), ("w)/",  "ὤ"), ("w(/",  "ὥ"), ("w)=",  "ὦ"), ("w(=",  "ὧ"),
    ("w)",   "ὠ"), ("w(",   "ὡ"), ("w\\",  "ὼ"), ("w/",   "ώ"), ("w=",   "ῶ"),
    ("w|",   "ῳ"),
    # Plain uppercase letters
    ("*a",  "Α"), ("*b",  "Β"), ("*g",  "Γ"), ("*d",  "Δ"), ("*e",  "Ε"),
    ("*z",  "Ζ"), ("*h",  "Η"), ("*q",  "Θ"), ("*i",  "Ι"), ("*k",  "Κ"),
    ("*l",  "Λ"), ("*m",  "Μ"), ("*n",  "Ν"), ("*c",  "Ξ"), ("*o",  "Ο"),
    ("*p",  "Π"), ("*r",  "Ρ"), ("*s3", "Ϲ"), ("*s",  "Σ"), ("*t",  "Τ"),
    ("*u",  "Υ"), ("*f",  "Φ"), ("*x",  "Χ"), ("*y",  "Ψ"), ("*w",  "Ω"),
    ("*v",  "Ϝ"),
    # Plain lowercase letters
    ("a",   "α"), ("b",   "β"), ("g",   "γ"), ("d",   "δ"), ("e",   "ε"),
    ("z",   "ζ"), ("h",   "η"), ("q",   "θ"), ("i",   "ι"), ("k",   "κ"),
    ("l",   "λ"), ("m",   "μ"), ("n",   "ν"), ("c",   "ξ"), ("o",   "ο"),
    ("p",   "π"), ("r",   "ρ"), ("s1",  "σ"), ("s2",  "ς"), ("s3",  "ϲ"),
    ("s",   "σ"), ("t",   "τ"), ("u",   "υ"), ("f",   "φ"), ("x",   "χ"),
    ("y",   "ψ"), ("w",   "ω"), ("v",   "ϝ"), ("#",   "ʹ")
]


class BetacodeError(Exception):
    def __init__(self, input_, error):
        self.input_ = input_
        self.error = error
    def __str__(self):
        return "failed decoding {} at '{}'".format(self.input_, self.error)


# make the prefix tree from all that crap ^up^ there.
def mk_trie(subl):
    trie = [None, {}]
    for sub in subl:
        branch = trie
        for c in sub[0]:
            branch = branch[1].setdefault(c, [None, {}])
        branch[0] = sub[1]
    return trie


# find matches in the trie
def climb(trie, fruit):
    branch = trie
    remainder = fruit
    for c in fruit:
        try:
            branch = branch[1][c]
        except KeyError:
            return (branch[0], remainder)
        remainder = remainder[1:]
    return (branch[0], remainder)


def decode(betacode):
    """
    performs substitutions by looking up characters from the string in a prefix
    tree. Fast for short words and phrases. Use betacode.decode() for longer
    strings.
    """
    code = betacode.lower()
    decoded_l = []
    while code:
        sub, code = climb(sub_trie, code)
        if not sub:
            sub = code[0]
            code = code[1:]
            if sub not in " .;?,:'-\"":
                raise BetacodeError(betacode, sub+code)
            if decoded_l[-1] == 'σ':
                decoded_l[-1] = 'ς'
        decoded_l.append(sub)
    if decoded_l[-1] == 'σ':
        decoded_l[-1] = 'ς'
    decoded = ''.join(decoded_l)
    return decoded
sub_trie = mk_trie(subl)


def decode_long(betacode):
    """\
    Iterates on substitutions for all possible betacode entities. Good for
    longer texts, like paragraphs or more. Use betacode.trie_decode() for
    iterating on lots of short texts (like words or phrases).
    """
    import re
    betacode = betacode.lower()
    fsigmas = [(r's([,.;:])',              r'ς\1'),
               (r's(\s)',                  r'ς\1'),
               (r's$',                        'ς'),
               (r"s([a-zA-Z/\\=[+]\-'])",  r'σ\1'),
               (r"s([^a-zA-Z/\\=[+]\-'])", r'ς\1')]
    for string, rep in subl:
        if string == 's':
            for p, r in fsigmas:
                betacode = re.sub(p, r, betacode)
        betacode = betacode.replace(string, rep)
    return betacode


def main()
    import sys
    #print(decode_long(sys.argv[1]))
    print(decode(sys.argv[1]))


if __name__ == '__main__':
    main()
