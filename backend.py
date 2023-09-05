class Backend:
    '''Backends are parsers that are intended to parse from text to objects,\
    so there is no `seq` or `alt` and the return value of `parse` can have other \
    types than `ParseResult`. Because of this, instead of producing a negative\
    `ParseResult`, they raise a `ParseError` in case of failure. Their only \
    resident is `parse`, which is of type `(ParseResult) -> a`'''

    def __init__(self, parse):
        self.parse = parse

def const(a):
    '''Const just returns the thing that is fed into it, no matter the string
    `char('1').attach(const(1))` parses '1' as int(1)'''
    return Backend(lambda _: a)
