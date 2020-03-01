import settings
import os
import datetime
import logging

def main():
    logger = logging.getLogger('automation')
    logger.info("Performing local repo cleanup...")

    def deleteOldFiles(folder, time_days):
        """
        check the folder for files that are older than the time_days and delete them

        :param folder:          (string) OS folder to check for old files
        :param time_days:       (int) files older than this number of days will be deleted
        :return:
        """

        for root, dirs, files in os.walk(folder, topdown=True):
            for name in files:
                file = os.path.join(root, name)
                file_date = datetime.date.fromtimestamp(os.path.getmtime(file))
                now = datetime.date.today()
                if now > file_date + datetime.timedelta(days=time_days):
                    os.remove(file)
                    logger.info(f'File: {file} is older than {time_days} days and has been deleted.')

    if settings.CLEANUP:
        deleteOldFiles(settings.DOWNLOAD_DIR, 1)

if __name__ == '__main__':
    main()
