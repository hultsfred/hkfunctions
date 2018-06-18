import os
import csv
import re

try:
    import xlrd
except ImportError as exc:
    print(exc)
    print(f"The module {exc.name} is required!")
try:
    import openpyxl
except ImportError as exc:
    print(exc)
    print(f"The module {exc.name} is required!")


def xl_export(filepath, sheet, start_row=2):
    """Hämtar data från en excelfil och returnerar en lista som kan användas
    i funktionen mssql_insert. Är det många rader så är den seg. Skulle vara
    interssant att jämföra denna i kombination med mssql_insert med.
    För alternativ se xl_to_csv"""
    try:
        wb = openpyxl.load_workbook(filename=filepath, data_only=True, read_only=True)
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


def xl_to_csv(inFile, outFile, sheet):
    """write docstring"""
    try:
        # print("xlsxToCsv")
        wb = xlrd.open_workbook(inFile)
        sh = wb.sheet_by_name(sheet)
        your_csv_file = open(outFile, "w", encoding="utf-8", newline="")
        wr = csv.writer(your_csv_file, delimiter="|")
        # print('xlsxToCsv')
        for rownum in range(sh.nrows):
            wr.writerow(sh.row_values(rownum))
        your_csv_file.close()
    except Exception as exc:
        print(exc)
        raise


def change_enc_one_file(outFile, s_decode="utf-8", d_encode="utf-16"):
    """write docstring"""
    print("changeEnc")
    with open(outFile, "rb") as source_file:
        target_file_name = outFile
        with open(target_file_name, "w+b") as dest_file:
            contents = source_file.read()
            dest_file.write(contents.decode(s_decode).encode(d_encode))


def change_enc_multiple_files(path, s_decode="utf-8", d_encode="utf-16"):
    """write docstring"""

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
            with open(target_file_name, "w+b") as dest_file:
                dest_file.write(contents.decode(s_decode).encode(d_encode))


def txt_to_csv(
    path,
    delete_original_file="Yes",
    encoding="utf-8",
    delimiter_outfile=";",
    delimiter_infile="",
):
    """
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
    """
    # add delete of originalfile

    file_list = os.listdir(path)
    for file in file_list:
        if os.path.splitext(file)[1] != ".txt":
            continue
        filename = os.path.splitext(file)[0]
        filepath_in = path + file
        filepath_out = path + filename + ".csv"
        with open(filepath_in, "r") as fin:
            if delimiter_infile == "":
                dialect = csv.Sniffer().sniff(fin.readline(), [",", ";", "\t", "|"])
                fin.seek(0)
            else:
                dialect = delimiter_infile
            in_file = csv.reader(fin, dialect)
            with open(filepath_out, "w", newline="", encoding=encoding) as fout:
                out_file = csv.writer(fout, delimiter=delimiter_outfile)
                out_file.writerows(in_file)
        if str.upper(delete_original_file).startswith("Y") or str.upper(
            delete_original_file
        ).startswith("J"):
            os.remove(filepath_in)


def list_to_csv(fullFilePath, result_list, csvType="w"):
    """ """
    try:
        if csvType == "w":
            with open(fullFilePath, "w", newline="\n") as f:
                writer = csv.writer(f, delimiter="|")
                writer.writerows(result_list)
        if csvType == "a":
            with open(fullFilePath, "a", newline="\n") as f:
                writer = csv.writer(f, delimiter="|")
                writer.writerows(result_list)
    except TypeError:
        pass


def checkDataForFaultyDelimiters(
    data, expected_number_of_delimiters, delimiter=";", start_row=0, end_row="LAST_ROW"
):
    """Checks if there are any rows that has to many delimiters and returns
    the total number of "bad rows".\n
    return: int\n
    Inputs:\n
    data = list of lists\n
    expected_number_of_delimiters = int\n
    delimiter = string. Default is ";"\n
    start_row = int. Default is the first row, i.e. index 0.\n
    end_row = int. Default is the last row, i.e. len(data)
    """
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


def correctFaultyDelimiter(data, position_of_faulty_delimiter, delimiter, replacement):
    """Byter endast ut en felaktig delimiter"""
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


def correctMultipleFaultyDelimiters(
    data,
    position_of_faulty_delimiter,
    delimiter,
    replacement,
    columns,
    start_row=0,
    end_row="LAST_ROW",
):
    """ Finds and replaces faulty delimiters in list of lists.
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
    """
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
