import os
import pandas
import glob
from collections import defaultdict
import logging
import xlsxwriter


def data_processing(file_dir, num_rows_skip, unique_keys, conditions_path, output_path, product_filters=None, drop_dups=False, duplicate_subset=None):
    """
    Build output data based on initial file within file_dir (takes most recent based on OS modified time) 
    and build indicators based on conditions_path and deliver final dataset to destination directory 
    (output_path).

    :param file_dir:             (string) absolute os path to init file directory
    :param num_rows_skip:        (int) number of rows to skip when reading in file
    :param unique_key            (list) the keys that uniquely identify the dataset
    :param conditions_path:      (string) absolute os path to conditions configuration file
    :param output_path:          (string) absolute os path to output directory
    :param product_filters:      (dict) key pairs of fields and their list of filters {name_of_column: [list_of_filter_values]}
    :param drop_dups             (bool) drop duplicate rows from output dataset?
    :param duplicate_subset      (list) columns that represent the subset to checked for duplicates 
    :return:                     None
    """
    logger = logging.getLogger('automation')
    logger.info('Beginning Preparation of data...')
    list_of_files = glob.glob(os.path.join(file_dir, '*.xlsx'))
    latest_file = max(list_of_files, key=os.path.getctime)
    df = pandas.read_excel(latest_file)

    # forward fill unnamed columns (which is the description of previous column)
    prev = None
    new_columns = list()
    current_columns = str(df.columns.values[0]).split(',')
    for column in current_columns:
        if column == '':
            rename = prev + ' Desc'
            new_columns.append(rename)
        else:
            new_columns.append(column)
        prev = column
    del df
    df = pandas.read_excel(latest_file, skiprows=num_rows_skip, names=new_columns)

    # limit dataset to necessary column filters
    if product_filters is not None:
        for column, to_apply in product_filters.items():
            for fltr in to_apply:
                df = df[df[str(column)].str.contains(str(fltr))]

    # open excel file outlining conditionals
    df_conditional = pandas.read_excel(conditions_path, sheet_name=None)
    sheets = df_conditional.keys()
    sheet_data = defaultdict(dict)
    # create dict of dicts that contains all of the sheet's conditional data
    for sheet in sheets:
        temp = dict()
        for column in df_conditional[sheet].columns.values:
            if column == 'Identifiers':
                identifiers = df_conditional[sheet][column].dropna()
                temp.update({'Identifiers': list(identifiers)})
            elif column == 'Exclude':
                exclude = df_conditional[sheet][column].dropna()
                temp.update({'Exclude': list(exclude)})
            elif column == 'Fields To Be Searched':
                to_search = df_conditional[sheet][column].dropna()
                temp.update({'To Search': list(to_search)})
        sheet_data.update({sheet: temp})

    def set_conditional(row, curr_sheet):
        # set row/column value to False if it is an excluded account
        for field in sheet_data[curr_sheet]['To Search']:
            if any(str(keyword).upper() in str(row[str(field)]).upper() for keyword in sheet_data[curr_sheet]['Exclude']):
                return False

        # set row/column value to True if it is in list of keyword identifiers
        for field in sheet_data[curr_sheet]['To Search']:
            if any(str(keyword).upper() in str(row[str(field)]).upper() for keyword in sheet_data[curr_sheet]['Identifiers']):
                return True

        # otherwise set to False
        return False

    # populate separate dataframes with new conditional columns
    dfs = dict()
    for sheet in sheets:
        df_name = 'df_' + str(sheet)
        temp_df = df.assign(conditional=df.apply(set_conditional, axis=1, curr_sheet=sheet))
        # rename conditional column name
        temp_df.rename(columns={'conditional': str(sheet)+' Indicator'}, inplace=True)
        dfs.update({df_name: temp_df})

    if len(dfs) == 1:
        df_complete = list(dfs.keys())[0]
    elif len(dfs) == 0:
        logger.warning("No data to write...")
        os._exit(0)
    else:
        df_complete = None
        for frame in dfs.values():
            if df_complete is None:
                df_complete = frame
            else:
                df_complete = pandas.merge(df_complete, frame, on=unique_keys, how='inner',
                                           suffixes=('', '_duplicate'))

    df_complete.drop(list(df_complete.filter(regex='_duplicate$')), axis=1, inplace=True)
    if drop_dups:
        df_complete.drop_duplicates(subset=duplicate_subset, inplace=True, keep='first')
    logger.info(df_complete.head)
    df_complete.to_excel(output_path, engine='xlsxwriter')
    logger.info('Data successfully written to: ' + str(output_path))
