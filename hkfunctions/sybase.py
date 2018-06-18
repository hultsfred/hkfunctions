try:
    import sqlanydb
except ImportError as exc:
    print(exc)
    print(f"The module {exc.name} is required!")


def query(server, db, query, user='', password=''):
    ''' TODO: write docstring'''

    conn = sqlanydb.connect(DSN=server, uid=user, pwd=password, dbn=db)
    try:
        cur = conn.cursor()
        cur.execute(query)
        result_list = cur.fetchall()
        conn.close()
        return result_list
    except Exception as exc:
        conn.close()
        print(exc)
        raise
    # Länk 1: http://stackoverflow.com/questions/8635818/multiple-insert-statements-vs-single-insert-with-multiple-values/8640583#8640583
    # Länk 2: http://stackoverflow.com/questions/29380383/python-pypyodbc-row-insert-using-string-and-nulls
    # Länk 3: http://infocenter.sybase.com/help/index.jsp?topic=/com.sybase.infocenter.dc01776.1600/doc/html/san1357754968070.html
