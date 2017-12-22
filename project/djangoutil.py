from collections import namedtuple


# https://docs.djangoproject.com/en/1.11/topics/db/sql/


# results['id'], results.get('id', None)
def dictfetchone(cursor):
    columns = [col[0] for col in cursor.description]
    data = cursor.fetchone()
    if data is None: data = ()

    return dict(zip(columns, data))


# results[0]['id'], results[0].get('id', None)
def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]

    return [dict(zip(columns, row)) for row in cursor.fetchall()]


# results[0].id, getattr(results[0], 'id', None)
def namedtuplefetchall(cursor):
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])

    return [nt_result(*row) for row in cursor.fetchall()]
