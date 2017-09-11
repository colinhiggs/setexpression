import json
import unittest

from ldap3 import (
    Server,
    Connection,
    MOCK_SYNC,
    LEVEL,
    SUBTREE,
    ALL_ATTRIBUTES
)

from setexpression.ldap import LDAPFilterSetExpression

def p(uid, quoted=False):
    '''Very simple constructor for person dns.'''
    dn = 'uid={},ou=people,ou=top'.format(uid)
    if quoted:
        dn = '"{}"'.format(dn)
    return dn

def g(cn, quoted=False):
    '''Very simple constructor for group dns.'''
    dn = 'cn={},ou=groups,ou=top'.format(cn)
    if quoted:
        dn = '"{}"'.format(dn)
    return dn

class TestLDAPFilterSetExpression(unittest.TestCase):

    def setUp(self):
        self.server = Server('test_server')
        self.con = Connection(
            self.server,
            client_strategy=MOCK_SYNC
        )
        self.con.strategy.entries_from_json('test-data.json')
        self.con.bind()
        self.expr = LDAPFilterSetExpression(
            json.loads(g('B', True)),
            connection=self.con,
            search_base='ou=people,ou=top'
        )

    def test_iter(self):
        '''Expression should work as an iterator.'''
        members = [member for member in self.expr]
        self.assertListEqual(sorted(members), [p(1), p(2)])

    def test_in(self):
        '''Expression should work as a container.'''
        self.assertIn(p(1), self.expr)

    def test_group_name(self):
        '''A group name expression. Check filter and correct membership.'''
        # Load the expression with a simple group name.
        self.expr.expression=json.loads(g('B', True))
        # Make sure we get the right filter.
        self.assertEqual(
            self.expr.evaluate(),
            '(memberOf={})'.format(g('B'))
        )
        # Make sure this results in the correct members.
        self.assertListEqual(sorted(self.expr.members), [p(1), p(2)])

    def test_direct_members(self):
        '''A member list expression. Check filter and correct membership.'''
        self.expr.expression=json.loads(
            '{{"{}": "null", "{}": null, "{}": null}}'.format(
                'uid=1', 'uid=2', 'uid=3'
            )
        )
        self.assertRegex(
            self.expr.evaluate(),
            r'\(\|\(uid=[1-3]\)\(uid=[1-3]\)\(uid=[1-3]\)\)'
        )
        self.assertListEqual(
            sorted(self.expr.members),
            [p(1), p(2), p(3)]
        )

    def test_union(self):
        '''A union expression. Check filter and correct membership.'''
        self.expr.expression=json.loads(
            '["union", "{}", "{}"]'.format(g('B'), g('C'))
        )
        self.assertEqual(
            self.expr.evaluate(),
            '(|(memberOf={})(memberOf={}))'.format(g('B'), g('C'))
        )
        self.assertListEqual(
            sorted(self.expr.members),
            [p(1), p(2), p(3)]
        )

    def test_intersect(self):
        '''An intersect expression. Check filter and correct membership.'''
        self.expr.expression=json.loads(
            '["intersect", "{}", "{}"]'.format(g('B'), g('C'))
        )
        self.assertEqual(
            self.expr.evaluate(),
            '(&(memberOf={})(memberOf={}))'.format(g('B'), g('C'))
        )
        self.assertListEqual(
            sorted(self.expr.members),
            [p(2)]
        )

    def test_not(self):
        '''A not expression. Check filter and correct membership.'''
        self.expr.expression=json.loads(
            '["not", "{}"]'.format(g('B'))
        )
        self.assertEqual(
            self.expr.evaluate(),
            '(!(memberOf={}))'.format(g('B'))
        )
        self.assertListEqual(
            sorted(self.expr.members),
            [p(3), p(4)]
        )

    def test_minus(self):
        '''A nminus expression. Check filter and correct membership.'''
        self.expr.expression=json.loads(
            '["minus", "{}", "{}"]'.format(g('B'), g('A'))
        )
        self.assertEqual(
            self.expr.evaluate(),
            '(&(memberOf={})(!(memberOf={})))'.format(g('B'),g('A'))
        )
        self.assertListEqual(
            sorted(self.expr.members),
            [p(2)]
        )


if __name__ == '__main__':
    unittest.main()
