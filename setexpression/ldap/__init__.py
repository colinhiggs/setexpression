'''Evaluate set expressions against LDAP groups.'''
import collections.abc
import ldap3

from setexpression import SetExpression


class LDAPFilterSetExpression(
        SetExpression, collections.abc.Iterable, collections.abc.Container
):
    '''Produce an LDAP filter from a set expression.'''

    def __init__(
            self, expression,
            connection=None,
            search_base=None, search_scope=ldap3.LEVEL, paged_size=100
    ):
        super().__init__(expression)
        self.connection = connection
        self.search_base = search_base
        self.search_scope = search_scope
        self.paged_size = paged_size

    def __iter__(self):
        return (
            item['dn'] for item in
            self.connection.extend.standard.paged_search(
                search_base=self.search_base,
                search_filter=self.evaluate(),
                search_scope=self.search_scope,
                paged_size=self.paged_size,
                generator=True
            )
        )

    def __contains__(self, test):
        search_filter = '(&({}){})'.format(test, self.evaluate())

        self.connection.search(
            search_base=self.search_base,
            search_scope=self.search_scope,
            search_filter=search_filter
        )
        return len(self.connection.entries) > 0

    @classmethod
    def __eval_group__(cls, name):
        return '(memberOf={})'.format(name)

    @classmethod
    def __eval_members__(cls, members):
        if len(members) == 1:
            return '({})'.format(next(iter(members)))
        return cls.__op_union__(*['({})'.format(member) for member in members])

    @classmethod
    def __op_intersect__(cls, *args):
        return "(&{})".format(''.join(args))

    @classmethod
    def __op_union__(cls, *args):
        return "(|{})".format(''.join(args))

    @classmethod
    def __op_not__(cls, *args):
        return "(!{})".format(args[0])

    @property
    def members(self):
        return [m for m in self]
