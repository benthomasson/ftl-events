
from durable.lang import m
from pyparsing import pyparsing_common, infix_notation, OpAssoc, one_of, ParserElement, QuotedString, ZeroOrMore, Combine
ParserElement.enable_packrat()
from ftl_events.condition_types import Identifier, String, OperatorExpression, Integer, Condition



integer = pyparsing_common.signed_integer.copy().add_parse_action(lambda toks: Integer(toks[0]))
ident = pyparsing_common.identifier
varname = Combine(ident + ZeroOrMore('.' + ident)).copy().add_parse_action(lambda toks: Identifier(toks[0]))


string1 = QuotedString("'").copy().add_parse_action(lambda toks: String(toks[0]))
string2 = QuotedString('"').copy().add_parse_action(lambda toks: String(toks[0]))

condition = infix_notation(integer | varname | string1 | string2,
                            [
                                ('!', 1, OpAssoc.RIGHT),
                                (one_of('* /'), 2, OpAssoc.LEFT),
                                (one_of('+ -'), 2, OpAssoc.LEFT),
                                (one_of('< >'), 2, OpAssoc.LEFT),
                                ('!=', 2, OpAssoc.LEFT, lambda toks: OperatorExpression(*toks[0])),
                                ('==', 2, OpAssoc.LEFT, lambda toks: OperatorExpression(*toks[0])),
                                ('>=', 2, OpAssoc.LEFT),
                                ('<=', 2, OpAssoc.LEFT),
                            ]).add_parse_action(lambda toks: Condition(toks[0]))

def parse_condition(condition_string: str) -> Condition:
    return condition.parseString(condition_string)[0]
