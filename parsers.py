from backend import Backend

RECURSE = 'recurse'

CODE_OK = 0
CODE_UNEXPECTED_CHAR = 1
CODE_UNEXPECTED_EOF = 2
CODES_GOOD = [CODE_OK]

class ParseError(BaseException):
    '''An error that is called when a `Backend` / `Sequencer` fails 

    `Backend` is meant to be the last in the chain

    `Sequencer` doesn't really have a sensible way of returning a bad `ParseResult`'''
    def __init__(self, s:str):
        self.s = s
    def __str__(self):
        return f"Parse Error: {self.s}"

class ParseResult:
    '''The class for a parse result. `result` is the string that got parsed, \
    `rest` is what's left.
    Possible results:
    - `OK` - `result` and `rest` have direct meaning
    - `Unexpected Char` - `result` is the unexpected character, `rest` is the whole \
        input string.
    - `Unexpected EOF` - `result` and `rest` are not used'''
    def __init__(self, result: str, rest: str, code: int):
        if code not in range(5):
            raise ValueError(f"Invalid code: `{code}`")
        self.result = result
        self.rest = rest
        self.code = code
    def __str__(self) -> str:
        match self.code:
            case 0: 
                return f"Result \"{self.result}\" \"{self.rest}\""
            case 1: 
                return f"Unexpected char \"{self.result}\""
            case 2:
                return f"Unexpected EOF"
            case 3:
                return f"Expected EOF"

class Parser(Backend):
    '''The basic parser class. Their only resident is the `parse` function, which \
        is of type `(str)->  ParseResult`. There are three methods:
         - combining parsers:
            - `seq` - sequence two parsers like a logical AND.

                `char('1').seq(char('2'))` will only parse `"12"`
            - `alt` - sequence two parsers like a logical OR.

                `char('1').alt(char('2'))` will either parse `'1'` or `'2'` \
                (if you give it `"12"` it will parse `'1'`)
         - attaching `Backend`s:
            - `attach` - apply a Backend to a Parser.

                `char('1').attach(Backend(lambda _: 1))` will parse '1' and \
                return an `int(1)`. If it fails, it will raise a `ParseError`
                You can't get the rest of the string after this, since the \
                `Backend` is supposed to be the last element in the chain.
            '''
    def __init__(self, parse):
        self.parse = parse
    def attach(self, end: Backend, result = False):
        '''Apply a Backend to a Parser.

        `char('1').attach(lambda _: 1)` will parse '1' and return an \
        `int(1)`. If it fails, it will raise a `ParseError`
        You can't get the rest of the string after this, since the \
        `Backend` is supposed to be the last element in the chain.'''
        def aux(i):
            res1 = self.parse(i)
            c, s = res1.code, res1.result
            if c not in CODES_GOOD:
                raise ParseError(str(res1))
            else:
                if result:
                    return end.parse(res1)
                else:
                    return end.parse(s)
        return Backend(aux)
                
    def seq(self, other):
        '''Sequence two parsers like a logical AND.

            `char('1').seq(char('2'))` will only parse `"12"`'''
        def aux(i):
            '''
            if other == RECURSE:
                f = aux
            else:
                f = other.parse
            '''
            f = other.parse
            res1 = self.parse(i)
            c, s, r = res1.code, res1.result, res1.rest
            if c not in CODES_GOOD:
                    return res1
            else:
                res2 = f(r)
                c1, s1, r1 = res2.code, res2.result, res2.rest
                if c1 not in CODES_GOOD:
                    return res2
                else:
                    return ParseResult(s + s1, r1, CODE_OK)
        return Parser(aux)
    def alt(self, other):
        '''Sequence two parsers like a logical OR.

            `char('1').alt(char('2'))` will either parse `'1'` or `'2'` \
            (if you give it `"12"` it will parse `'1'`)'''
        def aux(i):
            '''
            if other == RECURSE:
                f = aux
            else:
                f = other.parse
            '''
            f = other.parse
            res1 = self.parse(i)
            c, r = res1.code, res1.rest
            if c not in CODES_GOOD:
                return f(r)
            return res1
        return Parser(aux)

def _consume(i: str):
    if not i:
        return ParseResult('', '', CODE_UNEXPECTED_EOF)
    else:
        return ParseResult(i[0], i[1::], CODE_OK)

# Tries to parse any one character
consume = Parser(_consume)

# Always fails
fail = Parser(lambda i: ParseResult(i[0], i, CODE_UNEXPECTED_CHAR))

def char(c):
    '''Takes a `char` c (one character string) and parses one char if it's equal \
        to c
        
        `char(' ')` will parse exactly one space
        '''
    def aux(i: str) -> ParseResult:
        if not i:
            return ParseResult('', '', CODE_UNEXPECTED_EOF)
        elif i[0] == c:
            return ParseResult(c, i[1::], CODE_OK)
        else:
            return ParseResult(i[0], i, CODE_UNEXPECTED_CHAR)
    return Parser(aux)

def string(s):
    '''Like `char`, but with strs. Will remove the whole prefix if it matches \
       the given string.

       `string("123").parse("12345")` will parse `"123"` and leave `"45"`
    '''
    def aux(i: str):
        if not i:
            return ParseResult('', '', CODE_UNEXPECTED_EOF)
        elif i.startswith(s):
            return ParseResult(s, i.removeprefix(s), CODE_OK)
        else:
            return ParseResult(i[0], i, CODE_UNEXPECTED_CHAR)
    return Parser(aux)

def satisfy(f):
    '''Takes a predicate `f` of type `(char) -> Bool` (`char` is a single character \
        string). If the predicate is true, the parser will parse a single character \
        , otherwise returning an `Unexpected Char`
        
        `satisfy(lambda x: x in "1234567890")` will parse any one digit
        '''
    def aux(i: str):
        if not i:
            return ParseResult('', '', CODE_UNEXPECTED_EOF)
        elif f(i[0]):
            return ParseResult(i[0], i[1::], CODE_OK)
        else:
            return ParseResult(i[0], i, CODE_UNEXPECTED_CHAR)
    return Parser(aux)

def many(p: Parser):
    '''Take a parser and turns it into a praser that greedily triggers \
       0 or more times.
       
       `unds = many(char('_'))` will consume 0 or more spaces:
       - `unds.parse('123')` will return `result = ''` and `rest = "123"`
       - `unds.parse('____123')` will return `result = "____"` and `rest = "123"`
       '''
    def aux(i: str):
        res1 = p.parse(i)
        c, s, r = res1.code, res1.result, res1.rest
        if c not in CODES_GOOD:
            return ParseResult('', i, CODE_OK)
        else:
            res2 =  many(p).parse(r)
            s1, r1 = res2.result, res2.rest
            return ParseResult(s + s1, r1, CODE_OK)
    return Parser(aux)

def some(p: Parser):
    '''Take a parser and turns it into a praser that greedily triggers \
       1 or more times.
       
       `unds = some(char('_'))` will consume 1 or more spaces:
       - `unds.parse('123')` will return an `Unexpected Char` result
       - `unds.parse('____123')` will return `result = "____"` and `rest = "123"`
       '''
    return _some(p)

def _some(p: Parser, counter = 0):
    def aux(i: str):
        res1 = p.parse(i)
        c, s, r = res1.code, res1.result, res1.rest
        if c not in CODES_GOOD:
            if counter != 0:
                return ParseResult('', i, CODE_OK)
            else:
                return res1
        else:
            res2 = _some(p, counter = counter+1).parse(r)
            s1, r1 = res2.result, res2.rest
            return ParseResult(s + s1, r1, CODE_OK)
    return Parser(aux)

def surround(p: Parser, q: Parser = many(char(' '))):
    '''Returns `p` surrounded by `q`s using `seq` q is set to many(char(' ')) \
        by default.

       It's recommended to always `surround` your parsers, so that spaces won't play \
        a role in the source (unless you want significant whitespace, of course)
    '''
    return q.seq(p).seq(q)

