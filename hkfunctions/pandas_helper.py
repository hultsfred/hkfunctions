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
