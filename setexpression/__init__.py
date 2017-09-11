'''Handle JSON encoded set expressions.
'''
import abc
import json


class SetExpression(abc.ABC):
    '''Abstract base class for a set expression.'''

    def __init__(self, expression):
        self.expression = expression

    @classmethod
    def from_json(cls, _json):
        '''Construct an instance from a JSON string.'''
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
        '''Evaluate an expression.'''
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
        pass

    @classmethod
    @abc.abstractmethod
    def __op_intersect__(cls, *args):
        pass

    @classmethod
    @abc.abstractmethod
    def __op_not__(cls, *args):
        pass

    @classmethod
    @abc.abstractmethod
    def __eval_group__(cls, name):
        pass

    @classmethod
    @abc.abstractmethod
    def __eval_members__(cls, members):
        pass

    @classmethod
    def __op_minus__(cls, *args):
        return cls.__op_intersect__(
            args[0], *[cls.__op_not__(arg) for arg in args[1:]]
        )

    @classmethod
    def __expression_wrapper__(cls, expr):
        return expr
