__author__ = 'filadelfo'

""" https://www.dropbox.com/developers/core/sdks/python """
from dropbox.client import DropboxClient
from ConfigParser import ConfigParser
from os import path
import logging
import cStringIO

from nas import NasClient

__CFGFILE__ = "dboxcli.cfg"
__LOGSECTION_OPTION__ = ("LogSect","ext","level","fname")
__DROPBOXSECTION_OPTION__ = ("DBoxSect","tkn","dir")

__FORMATLOG__ = "%(asctime)-15s \%(message)s"

"""
Match files that start with prefix
"""
__FILEPATTERNMATCH__ = "DCS"

__STARTMSG__ = "Start.."
__INITMSG__ = "Connection to {device}.."
__INITMSG2__ = "Processing file actions.."
__ERRMSG1__ = "Error in configuration file {nomefile}\n---{raisemsg}----\n"
__ERRMSG2__ = "Errore during the access to {device}\n---{raisemsg}----\n"
__ERRMSG3__ = "Error during the file copy of {filename} on {device}\n---{raisemsg}----\n"
__ERRMSG4__ = "Error during the file removing of {filename} on {device}\n---{raisemsg}----\n"
__INFOFILE__ = "Files to be added {cnt_add}, Files to be removed {cnt_delete}\n"
__FILESUCCMSG__ = "File {filename} synced ({action})\n"
__SUCCMSG__ = "Completed"
__SUCCWARNMSG__ = "Completed with errors, check log files"

__ACCESS_TOKEN__ = None
__DROPBOXDIR__ = None
dropboxclient = None
dropboxfiles = None
nasclient = None
nasfiles = None
actions = None

def file_actions(master_dir_files, slave_dir_files):
    master_dir_files_cleaned = [f for f in master_dir_files if str(f).upper().startswith(__FILEPATTERNMATCH__)]
    master = set(master_dir_files_cleaned)
    slave = set(slave_dir_files)

    return {'ADD':master.difference(slave),'REMOVE':slave.difference(master)}

try:
    config = ConfigParser()
    config.read(__CFGFILE__)

    #### CONF ###
    __EXTFILE__ = config.get(__LOGSECTION_OPTION__[0], __LOGSECTION_OPTION__[1])
    __LEVELOG__ = getattr(logging,config.get(__LOGSECTION_OPTION__[0], __LOGSECTION_OPTION__[2]))
    __LOGFILE__ = config.get(__LOGSECTION_OPTION__[0], __LOGSECTION_OPTION__[3])

    __ACCESS_TOKEN__ = config.get(__DROPBOXSECTION_OPTION__[0], __DROPBOXSECTION_OPTION__[1])
    __DROPBOXDIR__ = config.get(__DROPBOXSECTION_OPTION__[0], __DROPBOXSECTION_OPTION__[2])
    ########

    logging.basicConfig(level=__LEVELOG__, filename=".".join([__LOGFILE__,__EXTFILE__]), format = __FORMATLOG__)
    logging.info(__STARTMSG__)

except Exception as e:
    logging.info(__ERRMSG1__.format(nomefile = __CFGFILE__,raisemsg = str(e)))
    exit(-1)



if all( [__ACCESS_TOKEN__,__DROPBOXDIR__] ):
    try:
        logging.info(__INITMSG__.format(device = "DropBox"))
        dropboxclient = DropboxClient(__ACCESS_TOKEN__)
        dropboxfiles = [path.basename(el['path']) for el in dropboxclient.metadata(__DROPBOXDIR__)['contents'] if not el['is_dir'] and el['bytes'] > 0]
    except Exception as e:
        logging.info(__ERRMSG2__.format(device="DropBox",raisemsg = str(e)))
        exit(-2)

if isinstance(dropboxfiles,list):
    try:
        logging.info(__INITMSG__.format(device = "Nas"))
        nasclient = NasClient()
        nasfiles = nasclient.getFileList()
    except Exception as e:
        logging.info(__ERRMSG2__.format(device="Nas",raisemsg = str(e)))
        exit(-3)

if isinstance(nasfiles,list):
    logging.info(__INITMSG2__)
    actions = file_actions(nasfiles,dropboxfiles)

anyerror = False
if actions:
    file_to_be_added = actions['ADD']
    file_to_be_removed = actions['REMOVE']

    logging.info(__INFOFILE__.format(cnt_add = str(len(file_to_be_added)), cnt_delete = str(len(file_to_be_removed))))
    
    """ Is there any faster way to get multiple files from the FTP Server? """
    for f in file_to_be_added:
        try:
            fp = cStringIO.StringIO()
            nasclient.getFile(f,fp)

            dropboxclient.put_file(path.join(__DROPBOXDIR__,f).replace("\\","/"),fp)
            fp.close()
            logging.info(__FILESUCCMSG__.format(filename = f, action = "ADD"))
        except Exception as e:
            logging.info(__ERRMSG3__.format(filename = f,device="Dropbox",raisemsg = str(e)))
            anyerror = True
            continue

    for f in file_to_be_removed:
        try:
            dropboxclient.file_delete(path.join(__DROPBOXDIR__,f).replace("\\","/"))
            logging.info(__FILESUCCMSG__.format(filename = f, action = "REMOVE"))
        except Exception as e:
            logging.info(__ERRMSG4__.format(filename = f,device="Dropbox",raisemsg = str(e)))
            anyerror = True
            continue

if anyerror:
    logging.info(__SUCCWARNMSG__)
else:
    logging.info(__SUCCMSG__)
