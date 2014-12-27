__author__ = 'filadelfo'

from ConfigParser import ConfigParser
from ftplib import FTP

__CFGFILE__ = "nascli.cfg"
__NASSECTION_OPTION__ = ("NasSect","ip","dir","username","pwd")

class NasClient():
    def __init__(self):
        config = ConfigParser()
        config.read(__CFGFILE__)

        try:
            #### CONF ###
            self.__host = config.get(__NASSECTION_OPTION__[0], __NASSECTION_OPTION__[1])
            self.__dir = config.get(__NASSECTION_OPTION__[0], __NASSECTION_OPTION__[2])
            self.__username = config.get(__NASSECTION_OPTION__[0], __NASSECTION_OPTION__[3])
            self.__pwd = config.get(__NASSECTION_OPTION__[0], __NASSECTION_OPTION__[4])
            ########

            self.__ftp_obj = FTP(self.__host)
            self.__ftp_obj.login(self.__username,self.__pwd)
            self.__successfullyConnected = True

            self.changeDirectory(self.__dir)

        except Exception as e:
            raise e

    def getFileList(self):
        _list_ = []
        if self.__successfullyConnected:
            try:
                _list_ = self.__ftp_obj.nlst()
            except:
                _list_ = []
        return _list_

    def changeDirectory(self, _dir_):
        _result = None
        if self.__successfullyConnected:
            try:
                _result = self.__ftp_obj.cwd(_dir_)
            except:
                _result = None
        return _result

    def getFile(self,filename,fp):
        _ret = False
        try:
            self.__ftp_obj.retrbinary('RETR %s' % filename, fp.write)
            _ret = True
        except:
            _ret = False
        return _ret
