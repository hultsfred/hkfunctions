try:
    import pandas as pd
except ImportError as exc:
    print(exc)
    print(f"The module {exc.name} is required!")

import warnings

def _from_dummies(dummy_df:pd.DataFrame, sep:str="_") -> pd.DataFrame:
    """recreates original dataframe passed in pd.get_dummies function
    
    :param dummy_df: [description]
    :type dummy_df: [type]
    :param sep: [description], defaults to "_"
    :param sep: str, optional
    :return: [description]
    :rtype: pd.DataFrame
    """
    try:
        stacked = pd.DataFrame(dummy_df.stack()).reset_index()
        stacked.columns = ["index_", "category", "value"]
        stacked = stacked[stacked["value"] == 1]
        name_categories = stacked.category.str.split(sep).tolist()
        column_name = name_categories[0][0]
        values = [i[1] for i in name_categories]
        from_dummies = pd.DataFrame(data={column_name: values}, index=stacked.index_)
        del from_dummies.index.name
    except IndexError as exc:
        print(exc)
        print("Possible reason is a dataframe with no specified dummy_columns")
        raise
    return from_dummies

def _from_dummies_helper(dummy_df, dummy_columns):
    noInputColumns = dummy_df.shape[1]
    dummy_columns_flattened = [i for sublist in dummy_columns for i in sublist]
    noNewColumns = len(dummy_columns)
    noDummyColumns = len(dummy_columns_flattened)
    return  dummy_columns_flattened, noInputColumns, noNewColumns, noDummyColumns

def from_dummies(dummy_df: pd.DataFrame, dummy_columns=None, value_columns:bool=False, sep:str="_") -> pd.DataFrame:
    """recreates original dataframe passed in pd.get_dummies function. For the function to work properly the paramaters
    'prefix' and 'prefix_sep' in pd.get_dummies must be set. E.g. 'prefix' can be set to name of the column that the 
    dummy columns are created from. The 'prefix_sep' should be set to a character that is not used in another column. 
    
    :param dummy_df: input dataframe, can have both dummy columns and value columns.
    :type dummy_df: pd.DataFrame
    :param dummy_columns: All dummy columns, for example [["A", "B"], ["C", "D"]]. Defaults to None
    :type dummy_columns: List of lists, optional
    :param value_columns: Should be set to True if there are columns in the original dataframe that are not dummy columns. Defaults to False.
    :type value_columns: bool, optional
    :param sep: seperator uses in pd.get_dummies, defaults to "_"
    :param sep: str, optional
    :return: [description]
    :rtype: pd.DataFrame
    """

    if not dummy_columns:
        return _from_dummies(dummy_df=dummy_df, sep=sep)
    if not isinstance(dummy_columns[0], list) == True:
        raise TypeError("The parameter 'dummy_columns' must be a list of lists!")
    
    dummy_columns_flattened, noInputCols, noNewColumns, noDummyColumns = _from_dummies_helper(dummy_df, dummy_columns)
    
    values = pd.DataFrame()
    if value_columns:
        values = dummy_df.drop(dummy_columns_flattened, axis=1)
        dummy_df = dummy_df.drop(values.columns, axis=1)
    from_dummies = pd.DataFrame()
    for i in dummy_columns:
        dummy = pd.DataFrame(dummy_df[i])
        temp = _from_dummies(dummy_df=dummy, sep=sep)
        from_dummies = pd.concat([from_dummies, temp], axis=1, ignore_index=False)
    if not values.empty:
        from_dummies = pd.concat([from_dummies, values], axis=1, ignore_index=False)
    noExpectedColumns = noInputCols - noDummyColumns + noNewColumns
    noOutColumns = from_dummies.shape[1]
    
    if noOutColumns != noExpectedColumns:
        warnings.warn(f"The expected number of columns in the output dataframe is {noExpectedColumns} and actual number of columns in the output dataframe is {noOutColumns}. If you have columns in the input dataframe that should be included in the output you must set the 'value_columns' parameter to True.")
    return from_dummies

def create_dummies(source: pd.DataFrame,
                   dummies: list,
                   iloc: bool=False,
                   target: pd.DataFrame=pd.DataFrame(),
                   prefix: bool=False) -> pd.DataFrame:
    """
    Creates dummies based on columns given in parameter dummies. If iloc is
    True index can be given
    """
    if iloc:
        columns = source.columns
        dummies = [columns[i] for i in dummies]
    if not target.empty:
        df = target
    else:
        df = pd.DataFrame()
    for i in dummies:
        if not prefix:
            prefix, prefix_sep = '', ''
        else:
            prefix, prefix_sep = i, '_'
        _temp = pd.get_dummies(data=source.loc[:, i], prefix=prefix, prefix_sep=prefix_sep)
        df = pd.concat([df, _temp], axis=1)
    return df
