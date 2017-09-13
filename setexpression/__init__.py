'''Handle JSON encoded set expressions.

Expressions in the form:

* set names: string
* list of members: dictionary keys
* set operations: array with [operator, arg1, arg2...]

Examples:

Assume we are working in LDAP.

* Sets are LDAP groupOfNames objects. Set names are their DNs.
* Members are the DNs of objects the might be group members.

Just group A:

"cn=A,ou=groups"

The union of A and B:

["union", "cn=A,ou=groups", "cn=B,ou==groups"]

A list of members:

{"uid=person1,ou=people": null, "uid=person2,ou=people": null}

The intersection of A and a list of members:

["intersect", "cn=A,ou=groups",
    {"uid=person1,ou=people": null, "uid=person2,ou=people": null}]

'''
import abc
import json


class SetExpression(abc.ABC):
    '''Abstract base class for classes representing set expressions.

    Abstract methods:
        * __op_union__
        * __op_intersect__
        * __op_not__
        * __eval_group__
        * __eval_members__
    '''

    def __init__(self, expression):
        '''Construct a new SetExpression.

        Arguments:
            expression: data structure (string, dictionary or array)
        '''
        self.expression = expression

    @classmethod
    def from_json(cls, _json):
        '''Construct an instance from a JSON string.

        Arguments:
            _json: JSON string
        '''
        return cls(json.loads(_json))

    def evaluate(self):
        '''Evaluate self.expression.'''
        return self.evaluate_expression(self.expression)

    @classmethod
    def evaluate_expression(cls, expr):
        '''Evaluate expr wrapped by __expression_wrapper__().'''
        return cls.__expression_wrapper__(cls.__eval_expression__(expr))

    @classmethod
    def __eval_expression__(cls, expr):
        '''Evaluate an expression.

        Fully evaluate an expression and return the result.

        Expressions in the form:

        * set names: string
        * list of members: dictionary keys
        * set operations: array with [operator, arg1, arg2...]

        Arguments:
            expr: data structure (string, dictionary or array)
        '''
        if isinstance(expr, list):
            # An expression (as an array): evaluate and return
            try:
                return getattr(cls, '__op_{}__'.format(expr[0]))(
                    *[cls.__eval_expression__(item) for item in expr[1:]]
                )
            except AttributeError:
                raise Exception('Unsupported operator "{}"'.format(expr[0]))
        elif isinstance(expr, str):
            # The dn of a group
            return cls.__eval_group__(expr)
        elif isinstance(expr, dict):
            # A set of direct member dns
            return cls.__eval_members__(expr)

    @classmethod
    @abc.abstractmethod
    def __op_union__(cls, *args):
        '''Return the union of arguments.'''
        pass

    @classmethod
    @abc.abstractmethod
    def __op_intersect__(cls, *args):
        '''Return the intersection of arguments.'''
        pass

    @classmethod
    @abc.abstractmethod
    def __op_not__(cls, *args):
        '''Return the negation (complement wrt the universal set) of the argument.'''
        pass

    @classmethod
    @abc.abstractmethod
    def __eval_group__(cls, name):
        '''Evaluate a group name.'''
        pass

    @classmethod
    @abc.abstractmethod
    def __eval_members__(cls, members):
        '''Evaluate a list of members expression.'''
        pass

    @classmethod
    def __op_minus__(cls, *args):
        '''Return args[0] minus all other arguments.'''
        return cls.__op_intersect__(
            args[0], *[cls.__op_not__(arg) for arg in args[1:]]
        )

    @classmethod
    def __expression_wrapper__(cls, expr):
        '''A wrapper for the entire expression.'''
        return expr
