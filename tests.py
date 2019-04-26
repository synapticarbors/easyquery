import numpy as np
from easyquery import Query

def test_valid_init():
    """
    test valid Query object creation
    """
    q1 = Query()
    q2 = Query(None)
    q3 = Query('x > 2')
    q4 = Query(lambda t: t['x'] > 2)
    q5 = Query((lambda c: c > 2, 'x'))
    q6 = Query('x > 2', lambda t: t['x'] > 2, (lambda c: c > 2, 'x'))
    q7 = Query(q3)
    q8 = Query(q3, 'x > 2')


def check_invalid_init(*queries):
    try:
        q = Query(*queries)
    except ValueError:
        pass
    else:
        raise AssertionError


def test_invalid_init():
    """
    test invalid Query object creation
    """
    for q in (1, [lambda x: x>1, 'a'], (lambda x: x>1,), ('a', lambda x: x>1)):
        check_invalid_init(q)


def gen_test_table():
    return np.array([(1, 5, 4.5), (1, 1, 6.2), (3, 2, 0.5), (5, 5, -3.5)],
                    dtype=np.dtype([('a', '<i8'), ('b', '<i8'), ('c', '<f8')]))


def check_query_on_table(table, query_object, true_mask=None):
    if true_mask is None:
        true_mask = np.ones(len(table), np.bool)

    assert (query_object.filter(table) == table[true_mask]).all(), 'filter not correct'
    assert query_object.count(table) == np.count_nonzero(true_mask), 'count not correct'
    assert (query_object.mask(table) == true_mask).all(), 'mask not correct'


def check_query_on_dict_table(table, query_object, true_mask=None):
    if true_mask is None:
        true_mask = np.ones(len(next(table.values())), np.bool)

    ftable = query_object.filter(table)
    ftable_true = {k: table[k][true_mask] for k in table}
    assert set(ftable) == set(ftable_true), 'filter not correct'
    assert all((ftable[k]==ftable_true[k]).all() for k in ftable), 'filter not correct'
    assert query_object.count(table) == np.count_nonzero(true_mask), 'count not correct'
    assert (query_object.mask(table) == true_mask).all(), 'mask not correct'


def test_simple_query():
    """
    test simple queries
    """
    t = gen_test_table()
    check_query_on_table(t, Query(), None)
    check_query_on_table(t, Query('a > 3'), t['a'] > 3)
    check_query_on_table(t, Query('a == 100'), t['a'] == 100)
    check_query_on_table(t, Query('b > c'), t['b'] > t['c'])
    check_query_on_table(t, Query('a < 3', 'b > c'), (t['a'] < 3) & (t['b'] > t['c']))


def do_compound_query(t, query_class, check_query):
    q1 = query_class('a == 1')
    m1 = t['a'] == 1
    q2 = query_class('a == b')
    m2 = t['a'] == t['b']
    q3 = 'b > c'
    m3 = t['b'] > t['c']

    q4 = ~~q2
    m4 = ~~m2
    q5 = q1 & q2 | q3
    m5 = m1 & m2 | m3
    q6 = ~q1 | q2 ^ q3
    m6 = ~m1 | m2 ^ m3
    q7 = q5 ^ q6
    m7 = m5 ^ m6
    q7 |= q2
    m7 |= m2
    q8 = q3 | q4
    m8 = m3 | m4
    q9 = q5.copy()
    m9 = m5

    check_query(t, q1, m1)
    check_query(t, q2, m2)
    check_query(t, q4, m4)
    check_query(t, q5, m5)
    check_query(t, q6, m6)
    check_query(t, q7, m7)
    check_query(t, q8, m8)
    check_query(t, q9, m9)


def test_compound_query():
    """
    test compound queries
    """
    do_compound_query(gen_test_table(), Query, check_query_on_table)


class DictQuery(Query):
    @staticmethod
    def _get_table_len(table):
        return len(next(table.values()))

    @staticmethod
    def _mask_table(table, mask):
        return {k: v[mask] for k, v in table.items()}


def test_derive_class():
    t = gen_test_table()
    t = {k: t[k] for k in t.dtype.names}
    do_compound_query(t, DictQuery, check_query_on_dict_table)


def test_variable_names():
    q1 = Query('log(a) > b**2.0')
    q2 = Query((lambda x, y: x + y < 1, 'c', 'd'))
    q3 = q1 & 'a + 2'
    q4 = ~q2
    q5 = q1 ^ q2
    q6 = Query('sin(5)')
    q7 = Query()

    assert set(q1.variable_names) == {'a', 'b'}
    assert set(q2.variable_names) == {'c', 'd'}
    assert set(q3.variable_names) == {'a', 'b'}
    assert set(q4.variable_names) == {'c', 'd'}
    assert set(q5.variable_names) == {'a', 'b', 'c', 'd'}
    assert set(q6.variable_names) == set()
    assert set(q7.variable_names) == set()


def test_filter_column_slice():
    t = gen_test_table()
    q = Query('a > 2')
    assert (q.filter(t, 'b') == t['b'][t['a'] > 2]).all()
    q = Query('a > 2', 'b < 2')
    assert (q.filter(t, 'c') == t['c'][(t['a'] > 2) & (t['b'] < 2)]).all()
    q = Query(None)
    assert (q.filter(t, 'a') == t['a']).all()


if __name__ == '__main__':
    test_valid_init()
    test_invalid_init()
    test_simple_query()
    test_compound_query()
    test_derive_class()
    test_variable_names()
    test_filter_column_slice()
