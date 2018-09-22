try:
    import pandas as pd
except ImportError as exc:
    print(exc)
    print(f"The module {exc.name} is required!")


def from_dummies(dummy_df, sep="_") -> pd.DataFrame:
    """recreates original dataframe passed in pd.get_dummies function
    
    :param dummy_df: [description]
    :type dummy_df: [type]
    :param sep: [description], defaults to "_"
    :param sep: str, optional
    :return: [description]
    :rtype: pd.DataFrame
    """

    stacked = pd.DataFrame(dummy_df.stack()).reset_index()
    stacked.columns = ["index_", "category", "value"]
    stacked = stacked[stacked["value"] == 1]
    name_categories = stacked.category.str.split(sep).tolist()
    column_name = name_categories[0][0]
    values = [i[1] for i in name_categories]
    from_dummies = pd.DataFrame(data={column_name: values}, index=stacked.index_)
    del from_dummies.index.name
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
