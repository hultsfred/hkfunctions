import getpass
import sys
import logging
import time
import traceback
try:
    import pymssql
except ImportError as exc:
    print(exc)
    print(f"The module {exc.name} is required!")


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
        sql1 = f"""
            INSERT INTO {self.db_tbl_log} (created_at, integration, created_by, log_level,
            log_levelname, log, error, traceback) VALUES (
                (convert(datetime2(7), \'{tm}\')),
                \'{self.integration}\',
                \'{record.name}\',
                \'{record.levelno}\',
                \'{record.levelname}\',
                \'{self.log_info}\',
                """
        if self.log_error != 'NULL':
            sql2 = f"""
            \'{self.log_error}\',
            \'{self.log_traceback}\')
            """
        else:
            sql2 = f"""
            {self.log_error},
            {self.log_traceback})
            """
        sql = sql1 + sql2
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
                logger.info(f'{func.__name__} worked correctly')
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