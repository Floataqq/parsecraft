from parsers import Parser, ParseResult, ParseError, \
    CODE_OK, CODE_UNEXPECTED_EOF, CODES_GOOD

class Handler:
    '''Class to feed to `Sequencer`s. `parser` is the parser that our sequencer \
       should use, `use` is a bool value indicating whether to include the \
       `ParseResult` of this handler in `Sequencer` output'''
    def __init__(self, p: Parser, use: bool = True):
        self.parser = p
        self.use = use

def _concat_seq(ps: [Handler], /, strict = True):
    def aux(i):
        if not i:
            if strict and len(ps) != 0:
                raise ParseError(str(ParseResult('', '', CODE_UNEXPECTED_EOF)))
            return [ParseResult('', '', CODE_OK)]
        if not ps:
            return [ParseResult('', i, CODE_OK)]
        p = ps[0].parser
        res = p.parse(i)
        if res.code not in CODES_GOOD and strict:
            raise ParseError(str(res))
        else:
            if ps[0].use:
                return [res] + _concat_seq(ps[1::])(res.rest)
            else:
                return [] + _concat_seq(ps[1::])(res.rest)
    return aux

class Sequencer:
    '''Class that allows you to sequence multiple parsers and get a list of \
       uncombined `ParseResults`. Also raises a `ParseError` on failure'''
    def __init__(self, handlers: [Handler] = None, parse = None):
        '''Initialise with a list of handlers or a `parse` function of type \
           `(String) -> [ParseResult]` directly. `parse` has more precedence  \
           than the handler list'''
        if not parse:
            if handlers:
                parse = _concat_seq(handlers)
            else:
                raise ValueError(f"Did not provide handlers nor parse function in \
Sequencer constructor")
        self.handlers = handlers
        self.parse = parse
    
    def seq(self, other):
        def aux(i):
            res = self.parse(i)
            rest = res[-1].rest
            f = res[:-1:]
            s = other.parse(rest)
            return f + s

        return Sequencer(parse=aux)
    
    def alt(self, other):
        def aux(i):
            try:
                res = self.parse(i)
                return res
            except ParseError:
                return other.parse(i)
        return Sequencer(parse=aux)
    
