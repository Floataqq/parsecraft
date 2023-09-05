import string as s
import backend as b, parsers as p, sequencer as seq

separator = p.surround(p.char(','))
relation = p.surround(p.char(':'))

string = p.surround(
    p.surround(
        p.some(p.satisfy(lambda x: x in s.printable and x != '"')),
        p.char('"')
    )
)
number = p.surround(
    p.some(p.satisfy(lambda x: x in "1234567890"))
)
array_num = p.surround(
    p.surround(p.char('[')).seq(p.some(number.seq(separator)).seq(number)).seq(p.surround(p.char(']')))
).alt(
    p.surround(p.char('[')).seq(number).seq(p.surround(p.char(']')))
).alt(
    p.surround(p.char('[')).seq(p.surround(p.char(']')))
)
array_str = p.surround(
    p.surround(p.char('[')).seq(p.some(string.seq(separator)).seq(string)).seq(p.surround(p.char(']')))
).alt(
    p.surround(p.char('[')).seq(string).seq(p.surround(p.char(']')))
).alt(
    p.surround(p.char('[')).seq(p.surround(p.char(']')))
)

valid_value = string.alt(number)
kvp = seq.Sequencer([
    seq.Handler(string),
    seq.Handler(relation, use=False),
    seq.Handler(valid_value, use=False),
    seq.Handler(separator, use=False)
])

