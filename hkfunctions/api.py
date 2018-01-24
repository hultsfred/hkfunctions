"""
module that helps with everyday life :)
"""

import os
import csv
import re
import time
import logging
import io
import functools
from itertools import zip_longest
import getpass
import traceback
import pymssql
from openpyxl import load_workbook
import sqlanydb
import xlrd
import paramiko
import smtplib
from email.message import EmailMessage

# TODO: * write docstrings
#       * remove unneccasary comments
#       * translate doctrings written in Swedish to English


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
        raise TypeError('{} are invalid keyword arguments'.format(
            kwargs.keys()))
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


def sybase_query(server, db, query, user='', password=''):
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


def xl_export(filepath, sheet, start_row=2):
    '''Hämtar data från en excelfil och returnerar en lista som kan användas
    i funktionen mssql_insert. Är det många rader så är den seg. Skulle vara
    interssant att jämföra denna i kombination med mssql_insert med.
    För alternativ se xl_to_csv'''
    try:
        wb = load_workbook(filename=filepath, data_only=True, read_only=True)
        sheet = wb[sheet]
        data = []
        for row in sheet.iter_rows():
            data_row = []
            for cell in row:
                data_row += [cell.value]
            data += [data_row]
        start_row = start_row - 1
        result_list = [tuple(l) for l in data[start_row:]]
        return result_list
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
        raise TypeError('{} are invalid keyword arguments'.format(
            kwargs.keys()))
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


def xl_to_csv(inFile, outFile, sheet):
    '''write docstring'''
    try:
        # print("xlsxToCsv")
        wb = xlrd.open_workbook(inFile)
        sh = wb.sheet_by_name(sheet)
        your_csv_file = open(outFile, 'w', encoding='utf-8', newline='')
        wr = csv.writer(your_csv_file, delimiter='|')
        # print('xlsxToCsv')
        for rownum in range(sh.nrows):
            wr.writerow(sh.row_values(rownum))
        your_csv_file.close()
    except Exception as exc:
        print(exc)
        raise


def change_enc_one_file(outFile, s_decode='utf-8', d_encode='utf-16'):
    '''write docstring'''
    print("changeEnc")
    with open(outFile, "rb") as source_file:
        target_file_name = outFile
        with open(target_file_name, 'w+b') as dest_file:
            contents = source_file.read()
            dest_file.write(contents.decode(s_decode).encode(d_encode))


def change_enc_multiple_files(path, s_decode='utf-8', d_encode='utf-16'):
    '''write docstring'''

    for file in os.listdir(path):
        # print("denc_utf16_Kör: "+file)
        filepath = os.path.join(path, file)
        # filename = os.path.splitext(file)[0]
        with open(filepath, "rb") as source_file:
            contents = source_file.read()
            try:
                os.remove(filepath)
            except OSError:
                pass
            target_file_name = filepath
            with open(target_file_name, 'w+b') as dest_file:
                dest_file.write(contents.decode(s_decode).encode(d_encode))


def txt_to_csv(path,
               delete_original_file='Yes',
               encoding='utf-8',
               delimiter_outfile=';',
               delimiter_infile=''):
    '''
    This function loops through a chosen folder and changes a txt file to a
    csv file. Optinal changes to teh file is delieting the original file,
    reencoding, and change of the delimiter\n
    path = path of the txt file/s that should be converted to csv.\n
    delete_original_file = if yes the original file is deleted, default is yes\n
    encoding = encoding of the csvfile, default=utf-8.\n
    delimiter_outfile = delimiter of the csv file, default is ';'.\n
    delimiter_infile = if the delimiter of the txt file is known it can be
    specified here. Although it is not necassary if the delimiter is equal
    to one of the following: [',',';','\t','|']. If the delimiter not is one of
    these 4 then the function will throw an exception.
    '''
    # add delete of originalfile

    file_list = os.listdir(path)
    for file in file_list:
        if os.path.splitext(file)[1] != '.txt':
            continue
        filename = os.path.splitext(file)[0]
        filepath_in = path + file
        filepath_out = path + filename + ".csv"
        with open(filepath_in, 'r') as fin:
            if delimiter_infile == '':
                dialect = csv.Sniffer().sniff(fin.readline(),
                                              [',', ';', '\t', '|'])
                fin.seek(0)
            else:
                dialect = delimiter_infile
            in_file = csv.reader(fin, dialect)
            with open(
                    filepath_out, 'w', newline='', encoding=encoding) as fout:
                out_file = csv.writer(fout, delimiter=delimiter_outfile)
                out_file.writerows(in_file)
        if str.upper(delete_original_file).startswith('Y') or str.upper(
                delete_original_file).startswith('J'):
            os.remove(filepath_in)


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


def list_to_csv(fullFilePath, result_list, csvType='w'):
    ''' '''
    try:
        if csvType == 'w':
            with open(fullFilePath, 'w', newline='\n') as f:
                writer = csv.writer(f, delimiter='|')
                writer.writerows(result_list)
        if csvType == 'a':
            with open(fullFilePath, 'a', newline='\n') as f:
                writer = csv.writer(f, delimiter='|')
                writer.writerows(result_list)
    except TypeError:
        pass


def checkDataForFaultyDelimiters(data,
                                 expected_number_of_delimiters,
                                 delimiter=";",
                                 start_row=0,
                                 end_row="LAST_ROW"):
    '''Checks if there are any rows that has to many delimiters and returns
    the total number of "bad rows".\n
    return: int\n
    Inputs:\n
    data = list of lists\n
    expected_number_of_delimiters = int\n
    delimiter = string. Default is ";"\n
    start_row = int. Default is the first row, i.e. index 0.\n
    end_row = int. Default is the last row, i.e. len(data)
    '''
    ex = expected_number_of_delimiters
    d = delimiter
    st = start_row
    if end_row == "LAST_ROW":
        end = len(data)
    else:
        end = end_row
    count = 0
    for row in data[st:end]:
        for l in row:
            if len(re.findall(d, l)) > ex:
                count += 1
    return count


def correctFaultyDelimiter(data, position_of_faulty_delimiter, delimiter,
                           replacement):
    '''Byter endast ut en felaktig delimiter'''
    corrected_bad_rows = []
    n = position_of_faulty_delimiter
    d = delimiter
    rep = replacement
    for rows in data:
        r = str(rows).replace("[", "").replace("]", "")
        where = [m.start() for m in re.finditer(d, r)][n - 1]
        before = r[:where]
        # print(before)
        after = r[where:]
        # print(after)
        x = after.replace(d, rep, 1)
        newString = (before + x).replace("'", "")
        # print(newString)
        corrected_bad_rows.append(newString.split(d))
    return corrected_bad_rows


def correctMultipleFaultyDelimiters(data,
                                    position_of_faulty_delimiter,
                                    delimiter,
                                    replacement,
                                    columns,
                                    start_row=0,
                                    end_row="LAST_ROW"):
    ''' Finds and replaces faulty delimiters in list of lists.
    When to use: E.g. if there should be 5 columns in the data but there is
    more than four (4) delimiters the data is impossible to insert into a
    database. This function replaces the faulty delimiters and makes the
    data ok.\n
    return: list of lists\n
    Inputs:\n
    data = list of lists\n
    position_of_faulty_delimiter = integer, the position of the faulty
    delimiter, occurs in textfields\n
    delimiter = string. Default is ";"\n
    replacement = string, e.g. "_"\n
    columns = int, numnber of columns in the data.
    start_row = int. Default is the first row, i.e. index 0.\n
    end_row = int. Default is the last roe, i.e. len(data)
    '''
    corrected_data = []
    n = position_of_faulty_delimiter
    d = delimiter
    rep = replacement
    col = columns - 1
    st = start_row
    if end_row == "LAST_ROW":
        end = len(data)
    else:
        end = end_row
    for row in data[st:end]:
        count = len(re.findall(d, str(row)))
        if count > col:
            while count > col:
                r = str(row).replace("[", "").replace("]", "")
                where = [m.start() for m in re.finditer(d, r)][n - 1]
                before = r[:where]
                after = r[where:]
                after = after.replace(d, rep, 1)
                row = (before + after).replace("'", "")
                count = len(re.findall(d, row))
        else:
            row = str(row).replace("[", "").replace("]", "").replace("'", "")
        corrected_data.append(row.split(d))
    return corrected_data


def sftp_download(path, files, host, port, username, password):
    """
    write docstring
    """
    transport = paramiko.Transport((host, port))
    transport.connect(username=username, password=password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    try:
        for i in files:
            filepath = '/' + i
            localpath = path + i
            sftp.get(filepath, localpath)
        sftp.close()
    except:
        print('hej')
        sftp.close()
        raise


def grouper(iterable, n, fillvalue=None):
    """
    delar upp en iterable i n delar. Bra att ha vid frågor mot api när antalet tillåtna
    element är begränsat
    källa:
    https://stackoverflow.com/questions/434287/what-is-the-most-pythonic-way-to-iterate-over-a-list-in-chunks
    """

    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue='')


class LogDBHandler(logging.Handler):
    '''
    Customized logging handler that puts logs to the database.
    pymssql required
    '''

    def __init__(self, sql_conn, sql_cursor, db_tbl_log, integration_id):
        logging.Handler.__init__(self)
        self.sql_cursor = sql_cursor
        self.sql_conn = sql_conn
        self.db_tbl_log = db_tbl_log
        self.integration = integration_id

    def emit(self, record):
        # Set current time
        tm = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.created))
        # Clear the log message so it can be put to db via sql (escape quotes)
        self.log_msg = record.msg
        self.log_msg = self.log_msg.strip()
        self.log_msg = self.log_msg.replace('\'', '\'\'').split('|')
        if len(self.log_msg) > 1:
            self.log_info = str(self.log_msg[0])
            self.log_error = str(self.log_msg[1])
            self.log_traceback = str(self.log_msg[2])
        else:
            self.log_info = self.log_msg[0]
            self.log_error = 'NULL'
            self.log_traceback = 'NULL'
        # Make the SQL insert
        if self.log_error != 'NULL':
            sql = """
                INSERT INTO {} (created_at, integration, created_by, log_level,
                log_levelname, log, error, traceback) VALUES (
                    (convert(datetime2(7), \'{}\')),
                    \'{}\',
                    \'{}\',
                    \'{}\',
                    \'{}\',
                    \'{}\',
                    \'{}\',
                    \'{}\')
                """.format(self.db_tbl_log, tm, self.integration, record.name,
                           record.levelno, record.levelname, self.log_info,
                           self.log_error, self.log_traceback)
        else:
            sql = """
                INSERT INTO {} (created_at, integration, created_by, log_level,
                log_levelname, log, error, traceback) VALUES (
                    (convert(datetime2(7), \'{}\')),
                    \'{}\',
                    \'{}\',
                    \'{}\',
                    \'{}\',
                    \'{}\',
                    \'{}\',
                    \'{}\')
                """.format(self.db_tbl_log, tm, self.integration, record.name,
                           record.levelno, record.levelname, self.log_info,
                           self.log_error, self.log_traceback)

        try:
            self.sql_cursor.execute(sql)
            self.sql_conn.commit()
            self.sql_conn.close()
        except pymssql.Error as e:
            self.sql_conn.close()
            print(sql)
            print(str(e))
            print('CRITICAL DB ERROR! Logging to database not possible!')


def create_logger():
    """
    Creates a logging object and returns it\n
    TODO: * support for custom filename and path\n
          * same format as create_logger_db\n

    Example:\n

    from hkfunctions import create_logger_logger, exceptions\n
    logger = create_logger()\n
    @exceptions(logger)\n
    def test():\n
    code here
    """
    logger = logging.getLogger("example_logger")
    logger.setLevel(logging.INFO)

    # create the logging file handler
    fh = logging.FileHandler(r"test.log")

    fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(fmt)
    fh.setFormatter(formatter)

    # add handler to logger object
    logger.addHandler(fh)
    return logger


def create_logger_db(sqlConn, sqlCursor, dbTblLog, integration_id):
    """
    Creates a logging object and returns it. pymssql is necassary.\n
    Only one occureance of the decorator can be run in the sam file for some reason.\n
    If multiple functions should must run and be logged tehy must be in separate files\n

    Example:\n
    import pymssql\n
    from hkfunctions import create_logger_logger, exceptions\n
    CONN_LOG = pymssql.connect(SERVER, USER, PW, DB)\n
    CURSOR_LOG = CONN_LOG.cursor()\n
    @exception(create_logger_db(CONN_LOG, CURSOR_LOG, TABLE_LOG))\n
    def test():\n
    code here
    """
    logger = logging.getLogger(getpass.getuser())
    logger.setLevel(logging.INFO)
    logger.propagate = False  # disables log to console

    # Set logger
    eh = LogDBHandler(sqlConn, sqlCursor, dbTblLog, integration_id)
    # add handler to logger object
    logger.addHandler(eh)

    return logger


def exception(logger):
    """
    A decorator that wraps the passed in function and logs
    exceptions should one occur

    @param logger: The logging object
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                function = func(*args, **kwargs)
                logger.info('{} worked correctly'.format(func.__name__))
                return function
            except Exception as exc:
                # log the exception and traceback
                tb = traceback.format_exc()
                err = "There was an exception in "
                err += func.__name__
                err += "|"
                err += str(exc)
                err += "|"
                err += tb[37:]  # skips Traceback (most recent call last):
                logger.exception(err)
                # re-raise the exception
                raise

        return wrapper

    return decorator


def send_mail(server, from_, to, subject, **kwargs):
    '''
    write docstring
    '''
    messageHeader = kwargs.pop('messageHeader', None)
    messageBody = kwargs.pop('messageBody', None)
    if messageHeader and messageBody:
        message = messageHeader + '\n\n' + messageBody
    elif messageHeader:
        message = messageHeader
    elif messageBody:
        message = messageBody
    else:
        message = ''
    msg = EmailMessage()
    msg.set_content(message)
    msg['Subject'] = subject
    msg['From'] = from_
    msg['To'] = to
    s = smtplib.SMTP(server)
    try:
        s.send_message(msg)
    except Exception:
        s.quit()
    s.quit()
