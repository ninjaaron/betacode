'''
Helpers for decoding Greek and Hebrew betacode, such as one finds in
CATSS, TLG, Perseus Tufts, and other weird places.

While it is generally recommended to use the `greek` module for your
decoding needs, which is based on unicode composition and is generally
faster, the `old_greek` module, which uses a prefix tree, will catch
certain types of betacode errors that the new decoder does not, which
can be helpful if you suspect you are dealing with bad betacode.
'''
from betacode import greek, hebrew
