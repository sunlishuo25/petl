# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division

from tempfile import NamedTemporaryFile
from decimal import Decimal
import json

import pytest

from petl import fromjson, tojson
from petl.test.helpers import ieq


@pytest.mark.parametrize('lines', [False, True])
@pytest.mark.parametrize('header', [None, ['amount', 'count', 'constant']])
def test_fromjson_decoder_options(tmpdir, lines, header):
    records = [('{"amount": 0.12345678901234567890123456789, '
                '"count": 9007199254740993, "constant": NaN}'),
               '{"amount": -1.25, "count": 0, "constant": Infinity}']
    text = '\n'.join(records) if lines else '[' + ','.join(records) + ']'
    path = tmpdir.join('numbers.json')
    path.write(text)
    actual = fromjson(str(path), lines=lines, header=header,
                      parse_float=Decimal, parse_int=str,
                      parse_constant=lambda value: None)
    expected = [('amount', 'count', 'constant'),
                (Decimal('0.12345678901234567890123456789'),
                 '9007199254740993', None),
                (Decimal('-1.25'), '0', None)]
    assert list(actual) == expected
    assert list(actual) == expected


@pytest.mark.parametrize('header', [None, ['NAME', 'EXTRA']])
@pytest.mark.parametrize('custom_decoder', [False, True])
def test_fromjson_lines_object_hook(tmpdir, header, custom_decoder):
    def uppercase_keys(record):
        return {key.upper(): value for key, value in record.items()}

    class UppercaseDecoder(json.JSONDecoder):
        def __init__(self, *args, **kwargs):
            kwargs['object_hook'] = uppercase_keys
            json.JSONDecoder.__init__(self, *args, **kwargs)

    options = ({'cls': UppercaseDecoder} if custom_decoder else
               {'object_hook': uppercase_keys})
    path = tmpdir.join('objects.jsonl')
    path.write('{"name": "first", "extra": {"nested": 1}}\n'
               '{"name": "second"}\n')
    actual = fromjson(str(path), lines=True, header=header, missing='NA',
                      **options)
    expected = [('NAME', 'EXTRA'), ('first', {'NESTED': 1}), ('second', 'NA')]
    assert list(actual) == expected
    assert list(actual) == expected


@pytest.mark.parametrize('header', [None, ['value']])
def test_fromjson_lines_invalid_decoder_option(tmpdir, header):
    path = tmpdir.join('options.jsonl')
    path.write('{"value": 1}\n')
    with pytest.raises(TypeError):
        list(fromjson(str(path), lines=True, header=header,
                      unknown_decoder_option=True))


def test_fromjson_1():
    f = NamedTemporaryFile(delete=False, mode='w')
    data = '{"name": "Gilbert", "wins": [["straight", "7S"], ["one pair", "10H"]]}\n' \
           '{"name": "Alexa", "wins": [["two pair", "4S"], ["two pair", "9S"]]}\n' \
           '{"name": "May", "wins": []}\n' \
           '{"name": "Deloise", "wins": [["three of a kind", "5S"]]}'

    f.write(data)
    f.close()

    actual = fromjson(f.name, header=['name', 'wins'], lines=True)

    expect = (('name', 'wins'),
              ('Gilbert', [["straight", "7S"], ["one pair", "10H"]]),
              ('Alexa', [["two pair", "4S"], ["two pair", "9S"]]),
              ('May', []),
              ('Deloise', [["three of a kind", "5S"]]))

    ieq(expect, actual)
    ieq(expect, actual)  # verify can iterate twice


def test_fromjson_2():
    f = NamedTemporaryFile(delete=False, mode='w')
    data = '{"foo": "bar1", "baz": 1}\n' \
           '{"foo": "bar2", "baz": 2}\n' \
           '{"foo": "bar3", "baz": 3}\n' \
           '{"foo": "bar4", "baz": 4}\n'

    f.write(data)
    f.close()

    actual = fromjson(f.name, header=['foo', 'baz'], lines=True)

    expect = (('foo', 'baz'),
              ('bar1', 1),
              ('bar2', 2),
              ('bar3', 3),
              ('bar4', 4))

    ieq(expect, actual)
    ieq(expect, actual)  # verify can iterate twice


def test_tojson_1():
    table = (('foo', 'bar'),
             ('a', 1),
             ('b', 2),
             ('c', 2))
    f = NamedTemporaryFile(delete=False, mode='r')
    tojson(table, f.name, lines=True)
    result = []
    for line in f:
        result.append(json.loads(line))
    assert len(result) == 3
    assert result[0]['foo'] == 'a'
    assert result[0]['bar'] == 1
    assert result[1]['foo'] == 'b'
    assert result[1]['bar'] == 2
    assert result[2]['foo'] == 'c'
    assert result[2]['bar'] == 2


def test_tojson_2():
    table = [['name', 'wins'],
             ['Gilbert', [['straight', '7S'], ['one pair', '10H']]],
             ['Alexa', [['two pair', '4S'], ['two pair', '9S']]],
             ['May', []],
             ['Deloise', [['three of a kind', '5S']]]]
    f = NamedTemporaryFile(delete=False, mode='r')
    tojson(table, f.name, lines=True)
    result = []
    for line in f:
        result.append(json.loads(line))
    assert len(result) == 4
    assert result[0]['name'] == 'Gilbert'
    assert result[0]['wins'] == [['straight', '7S'], ['one pair', '10H']]
    assert result[1]['name'] == 'Alexa'
    assert result[1]['wins'] == [['two pair', '4S'], ['two pair', '9S']]
    assert result[2]['name'] == 'May'
    assert result[2]['wins'] == []
    assert result[3]['name'] == 'Deloise'
    assert result[3]['wins'] == [['three of a kind', '5S']]
