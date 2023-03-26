# -*- coding: utf-8 -*-
import os
import re
import zipfile
import tarfile

from module import log


# Constants used in configuration.
ZIP = 'zip'
GZIP = 'gzip'
BZ2 ='bz2'


from .config import load as load_config
PROCESS_CONF = load_config("data_process.conf")

from .filter import translate_tags


class ZipFiles(object):

    def __init__(self, source_dicts, zip_format=ZIP):
        """
        sample of source_dicts:
        [
            {
                'cwd': root path that of the source and that with a related
                       path into zip file,
                'paths': list of target dir or file (with related path),
                         could be regex
            },
        ]
        """
        self.source_dicts = source_dicts
        self.__writer = None
        self.__zip_format = zip_format


    def pack(self, output_file):
        if os.path.isabs(output_file):
            self.__abs_archive = output_file
        else:
            self.__abs_archive = os.path.join(os.getcwd(), output_file)

        self.__writer = self.__get_writer()
        if self.__writer:
            count = self.__process()
            self.__writer.close()
            if count > 0:
                log.event('Packfile saved: ', self.__abs_archive)
            else:
                log.warning('No file to pack!')
                try:
                    os.remove(self.__abs_archive)
                except:
                    log.exception()
                    return None

        return self.__abs_archive


    def __process(self):
        count = 0
        old_cwd = os.getcwd()

        try:
            for source_dict in self.source_dicts:
                if source_dict['cwd']:
                    os.chdir(source_dict['cwd'])

                for src_path in source_dict['paths']:
                    if os.path.isabs(src_path):
                        self.__compress(src_path)
                        count += 1

                    else:
                        for root, dirs, files in os.walk('.'):
                            for name in files:
                                path = os.path.normpath(os.path.join(root, name))
                                mo = re.match(src_path, path)
                                if mo:
                                    self.__compress(path)
                                    count += 1

                os.chdir(old_cwd)

        finally:
            os.chdir(old_cwd)

        return count


    def __compress(self, src_path):

        if isinstance(self.__writer, tarfile.TarFile):
            def write(s, a):
                self.__writer.add(s, a)
        else:  # zipfile.ZipFile
            def write(s, a):
                self.__writer.write(s, a , zipfile.ZIP_DEFLATED)

        if os.path.isfile(src_path):
            if os.path.abspath(src_path) != self.__abs_archive:
                write(src_path, src_path)
        else:
            for root, dirs, files in os.walk(src_path):
                for name in files:
                    src = os.path.join(root, name)
                    if os.path.abspath(src) != self.__abs_archive:
                        write(src, src_path)


    def __get_writer(self):
        zip_format = self.__zip_format
        if zip_format == ZIP:
            return zipfile.ZipFile(self.__abs_archive, 'w')
        elif zip_format == GZIP:
            return tarfile.open(self.__abs_archive, 'w:gz')
        elif zip_format == BZ2:
            return tarfile.open(self.__abs_archive, 'w:bz2')
        else:
            log.problem('Unsupported zip format: ', zip_format)


def zip_bin_files(zip_path, out_path, source_name, tau_max, tau_resolution):
    if isinstance(tau_max, int):
        tau_max = "%d" % tau_max
    if isinstance(tau_resolution, int):
        tau_resolution = "%d" % tau_resolution

    zipfiles = ZipFiles([{
        'cwd': zip_path,
        'paths': [
            PROCESS_CONF['BIN_FILE_PATTERN']
        ]
    }])
    for filename in os.listdir(zip_path):
        mo = re.search(PROCESS_CONF['BIN_FILE_PATTERN'], filename)
        if mo:
            mo_dict = mo.groupdict()
            zipfiles.pack(
                os.path.join(
                    out_path,
                    translate_tags(PROCESS_CONF['BINARY_ZIP_FILE_PATTERN'],
                                   source_name,
                                   mo_dict['init_time'],
                                   mo_dict['member_no'],
                                   tau_max,
                                   tau_resolution,
                                   )
                )
            )
            break
