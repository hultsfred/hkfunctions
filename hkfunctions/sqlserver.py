try:
    import pymssql
except ImportError as exc:
    print(exc)
    print(f"The module {exc.name} is required!")


def mssql_query(server, db, **kwargs):
    '''
    kwargs:
    user: Användarnamn, Default: empty string, i.e. ''
    password: Llöseord till server, Default: empty string, i.e. ''
    sp: Namnp på sp Default: None
    sp_parameters: Om parametrs ska skicka med till sp'n. ksa skrivas som en tuple utan namnet på variabeln, tex ('2017-10-01',)
                   Obs! Komma måste anges Default: None
    sp_return: om sp'n ska returna reultat, alllt utvöver None kan ages för att denna ska gälla. Default: None
    Ställer en fråga mot en databas och returnerar data i froma av en list.
    Om datatypen för en kolumn är DECIMAL ställer det till problem då
    resultatet blir i ett konstigt format, det står Decimal('123') istället
    för 123. Detta kan lösas genom att casta om kolumnen till float eller int
    (kanske finns bättre alternativ?).
    '''
    query = kwargs.pop('query', None)
    user = kwargs.pop('user', '')
    password = kwargs.pop('password', '')
    stored_procedure = kwargs.pop('sp', None)
    sp_parameters = kwargs.pop('sp_parameters', None)
    sp_return = kwargs.pop('sp_return', None)
    if kwargs:
        raise TypeError(f'{kwargs.keys()} are invalid keyword arguments')
    try:
        with pymssql.connect(
                server=server, database=db, user=user,
                password=password) as conn:
            with conn.cursor() as cur:
                if stored_procedure is None:
                    cur.execute(query)
                    result_list = cur.fetchall()
                    return result_list
                else:
                    if sp_parameters is None:
                        cur.callproc(stored_procedure, )
                        if sp_return is not None:
                            result_list = [r for r in cur]
                            return result_list
                        else:
                            conn.commit()
                    else:
                        cur.callproc(stored_procedure, sp_parameters)
                        if sp_return is not None:
                            result_list = [r for r in cur]
                            return result_list
                        else:
                            conn.commit()

    except Exception as exc:
        print(exc)
        raise


def mssql_insert(
        server, db, table=None, data=None,
        **kwargs):  # result_list, truncate='no', user='', password=''):
    ''' Funkar bara för MSSQL. Denna funktion är beroende av en lista.
    Denna lista är en input. Tex kan mssql_query och sybase_query användas.
    KAnske kan få den att fungera med excel också,kolla länk:
    http://davidmburke.com/2013/02/13/pure-python-convert-any-spreadsheet-format-to-list/
    '''
    result_list = data
    statement = kwargs.pop('statement', None)
    user = kwargs.pop('user', '')
    password = kwargs.pop('password', '')
    truncate = kwargs.pop('truncate', 'no')
    faulty_strings = kwargs.pop('faulty_strings', False)

    if kwargs:
        raise TypeError(f'{kwargs.keys()} are invalid keyword arguments')
    if result_list is not None and statement is not None:
        raise TypeError(
            'It is not possible to combine result_list and statement. Chose one.'
        )
    if result_list is None and statement is None:
        raise TypeError(
            'Either result_list or statement must be provided. Chose one.')
    if result_list is not None and table is None:
        raise TypeError(
            'A tablename must be provided when a result_list is provided')
    with pymssql.connect(
            server=server,
            database=db,
            user=user,
            password=password,
            autocommit=True) as conn:
        with conn.cursor() as cur:
            try:
                if result_list is not None:
                    error_list = []
                    if truncate.lower().startswith(
                            'y') or truncate.lower().startswith('j'):
                        sql = '''TRUNCATE TABLE ''' + table
                        cur.execute(sql)
                    if type(result_list[0]) == list:
                        result_list = [tuple(l) for l in result_list]
                    if len(result_list) <= 1000:  # 3
                        result_string = ','.join(
                            str(r) for r in result_list)  # 4
                        result_string = result_string.replace("None", "NULL")
                        statement = '''INSERT INTO ''' + table + ''' Values ''' + result_string  # 5
                        # print(statement)
                        cur.execute(statement)
                    else:
                        if faulty_strings is False:
                            for row in result_list:
                                try:
                                    row = str(row).replace("None", "NULL")
                                    #print(row)
                                    statement = '''INSERT INTO ''' + table + ''' Values ''' + row
                                    #print(statement)
                                    cur.execute(statement)
                                except Exception as exc:
                                    print(exc)
                                    error_list.append(row)
                                    continue
                        else:
                            for row in result_list:
                                try:
                                    result_string = []
                                    for r in row:  # 8
                                        r = ''.join(str(r).replace("'", "''"))
                                        #print(y)
                                        result_string.append(r)
                                    result_string = str(
                                        tuple(result_string))  # 6
                                    result_string = result_string.replace(
                                        "\'None\'", "NULL").replace('"',
                                                                    "'")  #7
                                    #print(result_string)
                                    statement = '''INSERT INTO ''' + table + ''' Values ''' + result_string
                                    #print(statement)
                                    cur.execute(statement)
                                except Exception as exc:
                                    error_list.append(result_string)
                                    continue
                    #if len(error_list) > 0:
                    #print(f'ERROR:\n{error_list}\nERROR)
                else:
                    cur.execute(statement)

            except:
                raise

    # 1: om result_list saknar data så ska funktiopnen avslutas. Görs det inte
    # så kan det bli fel om funktionen används i en for loop där en av looparna
    # saknar data.
    # 2: Uppkoppling mot destinationsdatabasen
    # 3: INSERT funkar endast för max 1000 rader
    # 4 & 6: execute kan ej hantera tuple
    # 5: variabel som INSERT data i destinationsdatabasen
    # http://stackoverflow.com/questions/6335839/python-how-to-read-n-number-of-lines-at-a-time
    # 7: För att kunna inserta datan får inte NULL vara string och det måste vara semicolon.
    # 8: denna for loop ser till att ' ersätts med '' inne i varke column. Detta gör att hela raden är string vilket gör att None i sjuab mpste specifiera \'


def bulk_insert(server,
                user,
                password,
                db,
                table,
                filepath,
                truncate='nej',
                firstrow=2,
                fieldterminator='|'):
    '''write docstring'''
    # print("bulk_insert")
    with pymssql.connect(
            server=server, database=db, user=user, password=password) as conn:
        with conn.cursor() as cur:
            try:
                if truncate.startswith('y') or truncate.startswith('j'):
                    sql = """
                    TRUNCATE TABLE %s
                    BULK INSERT %s
                    from %s
                    with
                    (
                    FIRSTROW=%s,
                    FIELDTERMINATOR= %s,
                    codepage='1252'
                    )
                    """ % (table, table, "'" + filepath + "'", firstrow,
                           "'" + fieldterminator + "'")
                    cur.execute(sql)
                    conn.commit()
                else:
                    sql = """
                    BULK INSERT %s
                    from %s
                    with
                    (
                    FIRSTROW=%s,
                    FIELDTERMINATOR= %s,
                    codepage='1252'
                    )
                    """ % (table, "'" + filepath + "'", firstrow,
                           "'" + fieldterminator + "'")
                    cur.execute(sql)
                    conn.commit()
            except Exception as exc:
                print(exc)
                raise
