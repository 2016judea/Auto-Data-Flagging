"""
Author:         Aidan Jude
Date:           3/1/2020
Description:    This script is used when wanting to call the user interface.

Logic Flow:
    1. Read in excel data
    3. Join data set with other file that has new flags and identifiers
    4. Deliver completed data as excel file

"""
import os
import repo_cleanup
from data_processing import data_processing
import tkinter
import json
import settings
import traceback
import logging


if __name__ == '__main__':
    # set up logger
    logger = logging.getLogger('automation')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    fileHandler = logging.FileHandler(os.path.join(os.getcwd(), 'automation.log'))
    fileHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(formatter)
    logger.addHandler(consoleHandler)
    logger.setLevel(logging.INFO)

    # load saved settings (if there are any)
    if os.path.isfile('user_interface_settings.json'):
        with open('user_interface_settings.json') as f:
            saved_settings = json.load(f)

    # user interface
    window = tkinter.Tk()
    window.title("Data Flagging Automation")
    window.geometry("500x750")
    header = tkinter.Label(window, text="Please enter the necessary settings below.", font='Helvetica 14 bold').pack()
    tkinter.Label(window, text="").pack()
    tkinter.Label(window, text="File Directory (where the starting file is located)").pack()
    file_dir_entry = tkinter.Entry(window, width="50")
    file_dir_entry.insert(0, saved_settings['file_dir'] if saved_settings['file_dir'] else '')
    file_dir_entry.pack()
    tkinter.Label(window, text="").pack()
    tkinter.Label(window, text="Configuration Directory (where column conditions file is located)").pack()
    conditions_path_entry = tkinter.Entry(window, width="50")
    conditions_path_entry.insert(0, saved_settings['conditions_path'] if saved_settings['conditions_path'] else '')
    conditions_path_entry.pack()
    tkinter.Label(window, text="").pack()
    tkinter.Label(window, text="Output Path (where data is written to, need to include name & extension of file)").pack()
    output_path_entry = tkinter.Entry(window, width="50")
    output_path_entry.insert(0, saved_settings['output_path'] if saved_settings['output_path'] else '')
    output_path_entry.pack()
    tkinter.Label(window, text="").pack()
    tkinter.Label(window, text="Number of rows to skip in initial file").pack()
    num_rows_skip_entry = tkinter.Entry(window, width="50")
    num_rows_skip_entry.insert(0, saved_settings['num_rows_skip'] if saved_settings['num_rows_skip'] else '')
    num_rows_skip_entry.pack()
    tkinter.Label(window, text="").pack()
    tkinter.Label(window, text="Unique Keys for dataset (separate with comma)").pack()
    unique_keys_entry = tkinter.Entry(window, width="50")
    unique_keys_entry.insert(0, saved_settings['unique_keys'] if saved_settings['unique_keys'] else '')
    unique_keys_entry.pack()
    tkinter.Label(window, text="").pack()
    tkinter.Label(window, text="Columns and their filters (enter them like this: {column: [filter1, filter2, etc]})").pack()
    product_filters_entry = tkinter.Entry(window, width="50")
    product_filters_entry.insert(0, saved_settings['product_filters'] if saved_settings['product_filters'] else '')
    product_filters_entry.pack()
    tkinter.Label(window, text="").pack()
    drop_dups_var = tkinter.IntVar()
    drop_dups_chk = tkinter.Checkbutton(window, text="Drop Duplicate Rows", variable=drop_dups_var)
    drop_dups_var.pack()
    tkinter.Label(window, text="").pack()
    tkinter.Label(window, text="Duplciate Column Subset (if any, separate with comma)").pack()
    duplicate_subset_entry = tkinter.Entry(window, width="50")
    duplicate_subset_entry.insert(0, saved_settings['duplicate_subset'] if saved_settings['duplicate_subset'] else '')
    duplicate_subset_entry.pack()
    tkinter.Label(window, text="").pack()
    save_settings_var = tkinter.IntVar()
    save_settings_chk = tkinter.Checkbutton(window, text="Save these settings for next time", variable=save_settings_var)
    save_settings_chk.pack()
    tkinter.Label(window, text="").pack()

    def getEntrys():
        file_dir = file_dir_entry.get()
        conditions_path = conditions_path_entry.get()
        output_path = output_path_entry.get()
        num_rows_skip = int(num_rows_skip_entry.get())
        unique_keys = str(unique_keys_entry.get()).split(',')
        product_filters = json.loads(str(product_filters_entry.get()))
        drop_dups = bool(drop_dups_var.get())
        duplicate_subset = str(duplicate_subset_entry.get()).split(',')

        if len(file_dir) == 0 or len(conditions_path) == 0 or len(output_path) == 0 or len(unique_keys) or len(num_rows_skip):
            tkinter.Label(window, text="Certain entries must be entered to successfully run automation...").pack()
            return
        else:
            # Save settings if checkbox is checked
            if save_settings_var.get():
                tkinter.Label(window, text="Saving settings...").pack()
                to_save = dict(file_dir=file_dir,
                               conditions_path=conditions_path,
                               output_path=output_path,
                               )
                with open('user_interface_settings.json', 'w') as fp:
                    json.dump(to_save, fp)
            # Run automation
            tkinter.Label(window, text="Starting automation...").pack()
            try:
                # cleanup old files
                repo_cleanup.main()
                tkinter.Label(window, text="Old automation files have been removed.").pack()

                # process and deliver data
                data_processing(file_dir=file_dir, num_rows_skip=num_rows_skip, unique_keys=unique_keys, conditions_path=conditions_path, \
                                output_path=output_path, product_filters=product_filters, drop_dups=drop_dups, duplicate_subset=duplicate_subset)
                tkinter.Label(window, text="Data has been processed and delivered.").pack()
                tkinter.Label(window, text="Automation ran successfully.").pack()

            except Exception as err:
                traceback.print_exc()
                logger.exception(str(err))
                tkinter.Label(window, text="Failure occurred during automation. Check automation.log file for details.").pack()

    tkinter.Button(text='Run Automation', command=getEntrys).pack()
    window.mainloop()
