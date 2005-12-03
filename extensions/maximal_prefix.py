########################################################################
#
# File:   maximal_prefix.py
# Author: Nathaniel Smith
# Date:   2003-06-09
#
# Contents:
#   MaximalPrefixMatcher
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Classes
########################################################################

_INFINITY = 0x20000000
"""For purposes of this file, this is a sufficiently close
approximation to infinity.  (The highest possible Unicode code point
is 0x10ffffff, which is smaller.)  Used for the upper bound
markers."""

_MINUS_ZERO = -1
"""A number smaller than the smallest possible Unicode code point,
used for search keys."""

_MINUS_INFINITY = -10
"""A number smaller than the smallest possible Unicode code point and
also smaller than _MINUS_ZERO, used for the lower bound markers."""

class MaximalPrefixMatcher(object):
    """Given a string, finds the maximal prefix from some set.

    Builds a database of prefixes, and then given a string returns the
    longest prefix in our database that is a prefix of the given
    string.  For example:

        >>> m = MaximalPrefixMatcher(["foo", "foobar", "quux"])
        >>> m["foobarbaz"]
        'foobar'
        >>> m["fooba"]
        'foo'
        >>> m["foo"]
        'foo'
        >>> m["fo"]
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
          File "maximal_prefix.py", line 206, in match
            raise KeyError, string
        KeyError: 'fo'

    Algorithm based on Lampson, Srinivasan and Varghese 1998 [1].  This
    code will make much more sense if you read their paper first.
    'match' operates in (both worst and average case) O(log_2 N) time,
    where N is the total number of prefixes.  Initialization and 'add'
    are both O(N).  (Adding multiple prefixes is just as cheap as adding
    a single prefix, though; if necessary this class could be made to
    batch prefix adds).

    Their algorithm operates over bitstrings, and requires each leaf
    node to hold two possible values (one if the query matches the leaf
    exactly, one if it does not).  We operate over strings, but there's
    no good way to write down maximal/minimal strings starting with a
    given prefix, so for keys we unpack each string into a tuple of
    integers, and then append a marker integer at the end.  There are
    three marker integers, chosen so that for any string,
       lower_marker(string) < query(string) < upper_marker(string)
    .  Because we have strict inequality, we don't need to track
    multiple values per leaf node; queries never match leafs exactly.

    [1] Lampson, Srinivasan and Varghese 1998, IP Lookups using Multiway
    and Multicolumn Search, in IEEE/ACM Transactions on Networking.
    http://wustl.edu/~varghese/PAPERS/bsearch.ps.Z or
    http://citeseer.nj.nec.com/95678.html .

    """

    def __init__(self, prefixes=[]):
        """Create a MaximalPrefixMatcher.

        'prefixes' - A sequence containing the initial list of prefixes
        to match against, as if provided to 'add'."""

        self._prefixes = tuple(prefixes)
        self._rebuild()


    def add(self, prefixes):
        """Add a sequence of prefixes to be matched against."""
        
        # Optimization note: it might make sense to call _rebuild()
        # lazily, i.e., batch up add()s until a call to match; this
        # makes multiple sequential calls to add() essentially free.
        self._prefixes = self._prefixes + tuple(prefixes)
        self._rebuild()


    def _str2key(self, string, marker):
        """Converts a string to our internal key type."""

        # Optimization note: could make this more space-efficient by
        # returning an array.array instead of a tuple.
        lst = map(ord, string)
        lst.append(marker)
        return tuple(lst)


    def _rebuild(self):
        """Rebuilds the prefix lookup tree.

        Must be called after any modifications to '_prefixes'."""

        # Tree structure does not make sense for the empty prefix list,
        # so we special-case it.
        if not self._prefixes:
            return

        # Optimization note: could make the sort() and munging much
        # cheaper by keeping the old munged_nodes list around rather
        # than reconstructing it from scratch on each insert; Python's
        # sort() is very efficient on almost-sorted data.
        def munge_low(prefix):
            return (self._str2key(prefix, _MINUS_INFINITY), 1, prefix)
        def munge_high(prefix):
            return (self._str2key(prefix, _INFINITY), 0, prefix)
        munged_nodes = map(munge_low, self._prefixes)
        munged_nodes += map(munge_high, self._prefixes)
        munged_nodes.sort()

        leaf_nodes = []
        stack = []
        for key, low, prefix in munged_nodes:
            # If we get to a node, it means we are less than it,
            # except for the far rightmost node.  But that special
            # case is handled in match().
            if low:
                # If the node is a low end of the range, then we're
                # outside the range, and into the next range out.  If
                # the node marks an outermost range, then we're
                # outside all ranges.
                if stack: value = stack[-1]
                else: value = None
                stack.append(prefix)
            else:
                was = stack.pop()
                if was != prefix:
                    raise Exception, "Bug: %s != %s" % (was, prefix)
                # If the node is a high end of the range, then we're
                # inside the range.
                value = prefix
            # Tuple: key, leafp, value
            leaf_nodes.append((key, 1, value))

        # Now build a tree of tuples from a bunch of leaf nodes.
        def tree(lst):
            "Returns (tree, maximal key)."
            if len(lst) == 1:
                return (lst[0], lst[0][0])
            midpoint = len(lst) // 2
            (left, left_max) = tree(lst[:midpoint])
            (right, right_max) = tree(lst[midpoint:])
            # < key goes to left, > key goes to right
            key = left_max
            # Tuple: key, leafp, left, right
            node = (key, 0, left, right)
            return (node, right_max)

        self._tree = tree(leaf_nodes)[0]

    def _print_tree(self, tree, indent_incr=4):
        """Prints a prefix tree for debugging."""

        def do_print(t, indent):
            if t[1]:
                (key, leafp, value) = t
                print (" " * indent + "Leaf node: " + repr(key) +
                       " for " + repr(value))
            else:
                (key, leafp, left, right) = t
                print " " * indent + "Node: " + repr(key)
                print " " * indent + "Left: "
                do_print(left, indent + indent_incr)
                print " " * indent + "Right: "
                do_print(right, indent + indent_incr)
        do_print(tree, 0)

    def match(self, string):
        """Finds the maximal prefix for the given string.

        Raises a 'KeyError' if there is no matching prefix.
        
        returns - The maximal prefix as a string."""

        # Tree structure does not make sense for the empty prefix list,
        # so we special-case it.
        if not self._prefixes:
            raise KeyError, string

        query = self._str2key(string, _MINUS_ZERO)
        node = self._tree
        while not node[1]:  # not a leaf
            if query > node[0]: # if we're strictly bigger...
                node = node[3]  # ...go right,
            else:               # otherwise...
                node = node[2]  # ...go left.
        # Got a leaf node, return its value.
        # The nodes are built so that node[2] is the correct value for
        # a query that is (slightly) less than node[0].  This is
        # always true if we get here, unless we are at the far
        # rightmost node, in which case we also collect all queries
        # that are bigger than anything.  We handle these queries as a
        # special case; they always have no prefix.
        if query < node[0]:
            prefix = node[2]
            if prefix is None:
                raise KeyError, string
            return prefix
        else:
            raise KeyError, string

    __getitem__ = match
    """Can be used as a dict mapping strings to their maximal prefix."""



########################################################################
# PyUnit tests
########################################################################

import unittest

class _MaximalPrefixMatcherTest(unittest.TestCase):
    def setUp(self):
        self.prefixes = ["foo", "bar", "foobar", "foobaz", "barbaz"]
        self.matcher = MaximalPrefixMatcher(self.prefixes)

    def failUnlessMatch(self, string, prefix):
        actual = self.matcher.match(string)
        self.failUnless(actual == prefix,
                        "Prefix for %s is not %s, but %s"
                        % (string, prefix, actual))

    def failIfMatch(self, string, matcher=None):
        if matcher is None:
            matcher = self.matcher
        self.failUnlessRaises(KeyError, matcher.match, string)

    def testEmptyMatcher(self):
        m = MaximalPrefixMatcher()
        self.failIfMatch("foo", m)

    def testExactPrefixes(self):
        for p in self.prefixes:
            self.failUnlessMatch(p, p)

    def testPrefixesPlusX(self):
        for p in self.prefixes:
            self.failUnlessMatch(p + "X", p)

    def testAdd(self):
        self.failUnlessMatch("fooquux", "foo")
        self.matcher.add(["fooquux"])
        self.failUnlessMatch("fooquux", "fooquux")
        self.failUnlessMatch("fooquuxblah", "fooquux")

    def testShorter(self):
        self.failUnlessMatch("fooba", "foo")
        self.failUnlessMatch("barba", "bar")
        self.failIfMatch("fo")
        self.failIfMatch("ba")

    def testBig(self):
        self.failIfMatch("xyzzy")

    def testSmall(self):
        self.failIfMatch("aaaaa")

unittest.makeSuite(_MaximalPrefixMatcherTest, "test")
    
if __name__ == "__main__":
    unittest.main()


########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
