### Telnet FTP Manager 2
# VER: 09.05.2025 12:18 PM
# 5/16/2026 - one of these days i'll replace this ancient ahh method with something that uses deframer over UDP

from ftplib import FTP as FtpClient
from ftplib import error_perm
from lib.telnetlib import Telnet as TelnetClient
import json, os
import logging

log = logging.getLogger(__name__)
#coloredlogs.install()

class TelFTPMan():
    def __init__(self, autostart:bool=False):
        '''The NEW and IMPROVED Telnet FTP Manager. 
        
        autostart (bool): If True, all connections will be started on init. Otherwise, you will need to load the config and start the connections manually.'''
        log.info(f"Initialized TFM 2")
        self.FTP = None
        self.TN = None
        self.conn_ip = None
        self.conn_u = None
        self.conn_p = None
        self.config_ok = False
        if autostart:
            self.config_ok = self.loadConnectionConfig() # default settings.json in cwd
            if self.config_ok:
                self.connect(True, True) # connect both FTP and Telnet

    def loadConnectionConfig(self, fp:str="settings.json"):
        log.info(f"Loading connection details from '{fp}'")
        config_pass = True
        if os.path.exists(fp):
            with open(fp, "r") as settings_file:
                settings = json.load(settings_file)
                settings_file.close()
            STAR = settings.get("Star", {})
            if not STAR: 
                log.error(f"Cannot load connection details from '{fp}'- NOT CONFIGURED!")
                config_pass = False
            self.conn_ip = STAR.get("IP", None)
            self.conn_u = STAR.get("User", None)
            self.conn_p = STAR.get("Password", None)
            if not self.conn_ip: 
                log.error(f"IP address not configured for target Star.")
                config_pass = False
            if not self.conn_u: 
                log.error(f"Username not configured for target Star.")
                config_pass = False
            if not self.conn_p:
                log.error(f"Password not configured for target Star.")
                config_pass = False
            if not config_pass: log.warning(f"Configuration pass failed! Please make sure your config in '{fp}' is valid.")
        else:
            log.error(f"Cannot load config from invalid path: '{fp}'")
            config_pass = False
        self.config_ok = config_pass
        return config_pass
    def connect(self, telnet:bool=True, ftp:bool=True):
        '''Connect Telnet and FTP clients to remote star.
        
        telnet (bool): Connects Telnet if True (default).
        ftp (bool): Connects FTP if True (default).'''
        if self.config_ok:
            if telnet: # initialize telnet connection
                self.TN = TelnetConnection(ip=self.conn_ip, username=self.conn_u, password=self.conn_p)
                self.TN.connect()
                if self.TN.connected:
                    log.debug(f"TELNET ({self.conn_ip}) - OK!")
                else:
                    log.error(f"TELNET ({self.conn_ip}) - FAIL")
            if ftp:
                self.FTP = FTPConnection(ip=self.conn_ip, username=self.conn_u, password=self.conn_p)
                self.FTP.connect()
                if self.FTP.connected:
                    log.debug(f"FTP ({self.conn_ip}) - OK!")
                else:
                    log.error(f"FTP ({self.conn_ip}) - FAIL")
        else:
            log.warning(f"Cannot connect clients - config either not loaded or invalid.")
    def disconnect(self):
        '''General "disconnect all" function. This will disconnect both FTP and Telnet.'''
        if self.TN:
            if self.TN.connected:
                log.debug(f"Disconnecting telnet for Star at {self.conn_ip}")
                self.TN.disconnect()
                log.info(f"Telnet disconnected. ({self.conn_ip})")
            else:
                log.debug(f"Telnet client is not currently connected ({self.conn_ip}) - no need to disconnect.")
        else:
            log.debug(f"There is no defined Telnet client ({self.conn_ip}) - no need to disconnect.")
        if self.FTP:
            if self.FTP.connected:
                log.debug(f"Disconnecting FTP for Star at {self.conn_ip}")
                self.FTP.disconnect()
                log.info(f"FTP disconnected. ({self.conn_ip})")
            else:
                log.debug(f"FTP client is not currently connected ({self.conn_ip}) - no need to disconnect.")
        else:
            log.debug(f"There is no defined FTP client ({self.conn_ip}) - no need to disconnect.")
        log.info(f"Disconnected all clients for {self.conn_ip}")
        

class FTPConnection():
    def __init__(self, ip:str, username:str, password:str):
        log.debug(f"Readying new FTP instance - {username}@{ip}")
        self.ip = ip
        self.username = username
        self.password = password
        self.ftp = None
        self.connected = False
    def connect(self):
        log.info(f"Connecting to Star FTP - {self.username}@{self.ip}")
        try:
            self.ftp = FtpClient(self.ip) # connect via IP
            self.ftp.login(user=self.username, passwd=self.password) # login
            log.info(f"Logged into FTP successfully. ({self.username}@{self.ip})")
            self.connected = True
        except:
            log.error(f"Could not connect to FTP! ({self.username}@{self.ip})", exc_info=True)
            self.connected = False
    def disconnect(self):
        log.info(f"Disconnecting from Star FTP - {self.username}@{self.ip}")
        try:
            self.ftp.quit()
            self.connected = False
            log.info(f"Disconnected from FTP successfully. ({self.username}@{self.ip})")
        except:
            log.error(f"Could not disconnect from FTP! ({self.username}@{self.ip}) - Maybe the connection is already inactive?", exc_info=True)
    def cd(self, dir_p:str="/tmp"):
        log.debug(f"Moving to directory '{dir_p}' on FTP.")
        try:
            self.ftp.cwd(dir_p)
            log.debug(f"Moved to '{dir_p}' successfully.")
        except error_perm as e:
            log.error(f"Couldn't cd to '{dir_p}' - doesn't exist?")
        except:
            log.error(f"Unhandled exception.", exc_info=True)
    def upload(self, local_fp:str, remote_fname:str):
        '''local_fp: File path of the file on the local machine to be uploaded to the remote. (str)
        remote_fname: The new name of the uploaded file as it will appear on the remote machine. (str)'''
        if self.ftp.pwd() != "/":
            remote_output_path = f"{self.ftp.pwd()}/{remote_fname}'"
        else:
            remote_output_path = f"{remote_fname}"
        log.debug(f"UPLOAD: '{local_fp}' TO '{remote_output_path}' ON {self.ip}")
        if self.connected:
            if os.path.exists(local_fp):
                try:
                    tmp_fb = open(local_fp, "rb")
                    self.ftp.storbinary("STOR " + remote_fname, tmp_fb)
                    log.info(f"Successfully uploaded '{remote_output_path}'. ({self.ip})")
                except:
                    log.error(f"Couldn't store binary data of '{local_fp}' to remote host. ({self.ip})", exc_info=True)
            else:
                log.warning(f"Can't upload nonexistant local file path: '{local_fp}'")
        else:
            log.warning(f"Can't upload file - not connected to FTP at {self.ip}.")
    def listdir(self, remote_dir:str):
        '''Returns a list of files in the specified remote directory.'''
        log.debug(f"Listing remote directory: '{remote_dir}'")
        if self.connected:
            try:
                files = self.ftp.nlst(remote_dir)
                log.debug(f"LS DIR {remote_dir}: {files}")
                return files
            except error_perm as e:
                if str(e).startswith("550"):
                    log.info(f"Directory '{remote_dir}' is empty.")
                    files = []
                    return files
        else:
            log.warning(f"Can't list directory - FTP not connected.")
    def makedir(self, remote_dir:str):
        '''Make directory specified by string. Please remember any path not beginning with / will be relative to the current working directory.'''
        log.debug(f"Creating directory: '{remote_dir}'")
        if remote_dir == "/":
            log.error(f"Cannot overwrite directory '{remote_dir}' - this is the root location.")
        else:
            if self.connected:
                try:
                    self.ftp.mkd(remote_dir)
                    log.info(f"Successfully created directory: '{remote_dir}'")
                except error_perm as e:
                    if str(e).startswith("550"):
                        log.info(f"Directory '{remote_dir}' already exists on the remote. ({self.ip}).")
                    else:
                        raise
            else:
                log.error(f"Can't create directory '{remote_dir}' on {self.ip} - FTP client not connected.")
    def makedirs(self, remote_dir:str):
        '''Makes every directory in a path specified by string. Please remember any path not beginning with / will be relative to the current working directory.'''
        if remote_dir == "/":
            log.error(f"Cannot overwrite directory '{remote_dir}' - this is the root location. Besides, this function is to create multiple dirs anyway...")
        else:
            dirs_to_make = remote_dir.strip("/").split("/")
            folder_progress = ""
            for i in range(len(dirs_to_make)):
                current_folder = dirs_to_make[i]
                if i == 0 and remote_dir.startswith("/"): # append / to the first dir if the dir string started from root
                    current_folder = f"/{current_folder}"
                elif i != 0:
                    current_folder = f"/{current_folder}" # append / to subfolders to complete the path
                folder_progress += current_folder
                # make this piece of the extended dir
                self.makedir(folder_progress)
            log.debug(f"Made complete path: {folder_progress}")
    def dir_exists(self, dir_p:str):
        '''Attempts to cd to a directory to check if it exists. Returns boolean value. True if present, False if not.'''
        current_dir = self.ftp.pwd()
        try:
            self.ftp.cwd(dir_p)
            log.debug(f"Directory '{dir_p}' exists on the remote host.")
            self.ftp.cwd(current_dir) # return to the original directory
            return True
        except:
            self.ftp.cwd(current_dir)
            log.debug(f"Directory '{dir_p}' does not exist on remote host.")
            return False
            


class TelnetConnection():
    def __init__(self, ip:str, username:str, password:str):
        log.debug(f"Readying new FTP instance - {username}@{ip}")
        self.ip = ip
        self.username = username
        self.password = password
        self.telnet = None
        self.connected = False
    def connect(self):
        log.debug(f"Connecting to Star telnet - {self.username}@{self.ip}")
        try:
            log.debug(f"Attempting telnet login sequence.")
            self.telnet = TelnetClient(host=self.ip)
            self.telnet.read_until(b"login: ", 10)
            # new ascii text (username)
            log.debug(f"Got login prompt, writing username '{self.username}'")
            ascii_text = self.username.encode('ascii') # EVERY PIECE OF TEXT NEEDS TO BE WRITTEN TO THE TELNET CONNECTION AS ASCII
            self.telnet.write(ascii_text + b"\n") # write the username (ASCII) and hit "enter" (new line)
            self.telnet.read_until(b"Password:", 10)
            # new ascii text (password)
            log.debug(f"Got password prompt, writing password...")
            ascii_text = self.password.encode('ascii')
            self.telnet.write(ascii_text + b"\n") # write the password as ascii and hit enter
            self.telnet.read_until(b"# ", 10)
            log.debug(f"Received terminal... (in hacker voice): I'm in.")
            log.info(f"Logged into telnet successfully. ({self.username}@{self.ip})")
            self.connected = True
        except EOFError:
            log.error(f"Telnet connection was closed abruptly. ({self.username}@{self.ip})", exc_info=True)
            self.connected = False
        except:
            log.error(f"Could not connect to telnet! ({self.username}@{self.ip})", exc_info=True)
            self.connected = False
    def disconnect(self):
        log.debug(f"Disconnecting from Star telnet - {self.username}@{self.ip}")
        if self.connected:
            try:
                log.debug(f"Writing 'exit' to terminal ({self.ip})")
                ascii_text = bytes("exit\n", "ascii")
                self.telnet.write(ascii_text)
                log.debug(f"Closing the telnet connection by force.")
                self.telnet.close()
                self.connected = False
                log.info(f"Successfully disconnected from telnet. ({self.username}@{self.ip})")
            except EOFError:
                log.error(f"Telnet connection was closed abruptly. ({self.username}@{self.ip})", exc_info=True)
                self.connected = False
            except:
                log.error(f"Could not connect to telnet! ({self.username}@{self.ip})", exc_info=True)
                self.connected = False
        else:
            log.warning(f"No need to disconnect telnet - session already inactive? ({self.username}@{self.ip})")
    def write(self, string:str, timeout:int=10):
        '''Write to the connected telnet terminal. Returns terminal output.
        
        string (str): Text to write to terminal. New line will automatically be appended (enter).
        timeout (int): Wait time to receive new commandline after writing the text.'''
        string = f"{string}\n" # append new line (enter key) to the terminal
        ascii_text = bytes(string, "ascii") # encode whatever as ascii
        if self.connected:
            try:
                log.debug(f"Writing '{string}' to terminal - await {timeout} second timeout. ({self.username}@{self.ip})")
                self.telnet.write(ascii_text)
                term_out = self.telnet.read_until(b"# ", timeout=timeout)
                log.debug(f"SUCCESS - got terminal.\nThis is the output of the terminal, in case you wanted it:\n{term_out}")
                return term_out
            except EOFError:
                log.error(f"Telnet connection was closed abruptly. ({self.username}@{self.ip})", exc_info=True)
                self.connected = False
            except:
                log.error(f"Could not connect to telnet! ({self.username}@{self.ip})", exc_info=True)
                self.connected = False
        else:
            log.warning(f"Cannot write to terminal - telnet connection is closed?")
    def cd(self, remote_dir:str):
        '''remote_dir (str): Path to desired working directory on the remote machine.'''
        term_cmd = f"cd {remote_dir}"
        self.write(string=term_cmd)
        log.debug(f"OK - New working directory is '{remote_dir}', allegedly...")



if __name__ == "__main__":
    import coloredlogs
    coloredlogs.install(level="DEBUG")
    TFM = TelFTPMan(autostart=True)
    TFM.TN.write("echo HELLO WORLD")
    TFM.TN.cd("/twc/bin")
    #TFM.TN.write("echo \"CALL PE SNUP\" | /twc/bin/fire_str")
    TFM.FTP.listdir("/twc/v1")
    #TFM.FTP.makedir("/testtest2ftp")
    TFM.FTP.makedirs("/testing/multiple/ftp/paths")
    TFM.FTP.dir_exists("/testing/multiple/ftp/paths")
    TFM.FTP.dir_exists("/shit")
    #TFM.FTP.upload(local_fp="goop.txt", remote_fname="/tester129/huh/yeet.txt")
    TFM.disconnect()