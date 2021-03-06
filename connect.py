#!/usr/bin/python
#
# Copyright (c) 2016 Red Hat
# Luke Hinds (lhinds@redhat.com)
# This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# 0.1: OpenSCAP paramiko connection functions

import logging
import os
import socket

import paramiko


# add installer IP from env
INSTALLER_IP = os.getenv('INSTALLER_IP')

# Set up loggers
logger = logging.getLogger('security_scan')
paramiko.util.log_to_file("/var/log/paramiko.log")


class SetUp:
    def __init__(self, *args):
        self.args = args

    def keystonepass(self):
        """ Used to retrieve keystone password """
        com = self.args[0]
        client = paramiko.SSHClient()
        privatekeyfile = os.path.expanduser('/root/.ssh/id_rsa')
        selectedkey = paramiko.RSAKey.from_private_key_file(privatekeyfile)
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(INSTALLER_IP, port=22, username='stack',
                           pkey=selectedkey)
        except paramiko.SSHException:
            logger.error("Password is invalid for "
                         "undercloud host: {0}".format(INSTALLER_IP))
        except paramiko.AuthenticationException:
            logger.error("Authentication failed for "
                         "undercloud host: {0}".format(INSTALLER_IP))
        except socket.error:
            logger.error("Socker Connection failed for "
                         "undercloud host: {0}".format(INSTALLER_IP))
        stdin, stdout, stderr = client.exec_command(com)
        return stdout.read()
        client.close()

    def getockey(self):
        """ Used to retrieve, SSH overcloud keys """
        remotekey = self.args[0]
        localkey = self.args[1]
        privatekeyfile = os.path.expanduser('/root/.ssh/id_rsa')
        selectedkey = paramiko.RSAKey.from_private_key_file(privatekeyfile)
        transport = paramiko.Transport((INSTALLER_IP, 22))
        transport.connect(username='stack', pkey=selectedkey)
        try:
            sftp = paramiko.SFTPClient.from_transport(transport)
        except paramiko.SSHException:
            logger.error("Authentication failed for "
                         "host: {0}".format(INSTALLER_IP))
        except paramiko.AuthenticationException:
            logger.error("Authentication failed for "
                         "host: {0}".format(INSTALLER_IP))
        except socket.error:
            logger.error("Socker Connection failed for "
                         "undercloud host: {0}".format(INSTALLER_IP))
        sftp.get(remotekey, localkey)
        sftp.close()
        transport.close()


class ConnectionManager:
    def __init__(self, host, port, user, localkey, *args):
        self.host = host
        self.port = port
        self.user = user
        self.localkey = localkey
        self.args = args

    def remotescript(self):
        """ Function to execute remote scripts """
        localpath = self.args[0]
        remotepath = self.args[1]
        com = self.args[2]

        client = paramiko.SSHClient()
        privatekeyfile = os.path.expanduser('/root/.ssh/id_rsa')
        selectedkey = paramiko.RSAKey.from_private_key_file(privatekeyfile)
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(INSTALLER_IP, port=22, username='stack',
                           pkey=selectedkey)
        except paramiko.SSHException:
            logger.error("Authentication failed for "
                         "host: {0}".format(self.host))
        except paramiko.AuthenticationException:
            logger.error("Authentication failed for "
                         "host: {0}".format(self.host))
        except socket.error:
            logger.error("Socker Connection failed for "
                         "undercloud host: {0}".format(self.host))

        transport = client.get_transport()
        local_addr = ('127.0.0.1', 0)
        channel = transport.open_channel("direct-tcpip",
                                         (self.host, int(self.port)),
                                         (local_addr))
        remote_client = paramiko.SSHClient()
        remote_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            remote_client.connect('127.0.0.1', port=22, username=self.user,
                                  key_filename=self.localkey, sock=channel)
            sftp = remote_client.open_sftp()
            sftp.put(localpath, remotepath)
        except paramiko.SSHException:
            logger.error("Authentication failed for "
                         "host: {0}".format(self.host))
        except paramiko.AuthenticationException:
            logger.error("Authentication failed for "
                         "host: {0}".format(self.host))
        except socket.error:
            logger.error("Socker Connection failed for "
                         "undercloud host: {0}".format(self.host))

        output = ""
        stdin, stdout, stderr = remote_client.exec_command(com)
        stdout = stdout.readlines()
        sftp.remove(remotepath)
        remote_client.close()
        client.close()
        for line in stdout:
            output = output + line
        if output != "":
            return output

    def remotecmd(self):
        """ Used to execute remote commands """
        com = self.args[0]

        client = paramiko.SSHClient()
        privatekeyfile = os.path.expanduser('/root/.ssh/id_rsa')
        selectedkey = paramiko.RSAKey.from_private_key_file(privatekeyfile)
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(INSTALLER_IP, port=22, username='stack',
                           pkey=selectedkey)
        except paramiko.SSHException:
            logger.error("Authentication failed for "
                         "host: {0}".format(self.host))
        except paramiko.AuthenticationException:
            logger.error("Authentication failed for "
                         "host: {0}".format(self.host))
        except socket.error:
            logger.error("Socker Connection failed for "
                         "undercloud host: {0}".format(self.host))

        transport = client.get_transport()
        local_addr = ('127.0.0.1', 0)  # 0 denotes choose random port
        channel = transport.open_channel("direct-tcpip",
                                         (self.host, int(self.port)),
                                         (local_addr))
        remote_client = paramiko.SSHClient()
        remote_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            remote_client.connect('127.0.0.1', port=22, username=self.user,
                                  key_filename=self.localkey, sock=channel)
        except paramiko.SSHException:
            logger.error("Authentication failed for "
                         "host: {0}".format(self.host))
        except paramiko.AuthenticationException:
            logger.error("Authentication failed for "
                         "host: {0}".format(self.host))
        except socket.error:
            logger.error("Socker Connection failed for "
                         "undercloud host: {0}".format(self.host))

        chan = remote_client.get_transport().open_session()
        chan.get_pty()
        feed = chan.makefile()
        chan.exec_command(com)
        print feed.read()

        remote_client.close()
        client.close()

    def download_reports(self):
        """ Function to retrieve reports from remote nodes """
        dl_folder = self.args[0]
        reportfile = self.args[1]
        reportname = self.args[2]
        resultsname = self.args[3]
        client = paramiko.SSHClient()
        privatekeyfile = os.path.expanduser('/root/.ssh/id_rsa')
        selectedkey = paramiko.RSAKey.from_private_key_file(privatekeyfile)
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(INSTALLER_IP, port=22, username='stack',
                           pkey=selectedkey)
        except paramiko.SSHException:
            logger.error("Authentication failed for "
                         "host: {0}".format(self.host))
        except paramiko.AuthenticationException:
            logger.error("Authentication failed for "
                         "host: {0}".format(self.host))
        except socket.error:
            logger.error("Socker Connection failed for "
                         "undercloud host: {0}".format(self.host))

        transport = client.get_transport()
        local_addr = ('127.0.0.1', 0)  # 0 denotes choose random port
        channel = transport.open_channel("direct-tcpip",
                                         (self.host, int(self.port)),
                                         (local_addr))
        remote_client = paramiko.SSHClient()
        remote_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            remote_client.connect('127.0.0.1', port=22, username=self.user,
                                  key_filename=self.localkey, sock=channel)
        except paramiko.SSHException:
            logger.error("Authentication failed for "
                         "host: {0}".format(self.host))
        except paramiko.AuthenticationException:
            logger.error("Authentication failed for "
                         "host: {0}".format(self.host))
        except socket.error:
            logger.error("Socker Connection failed for "
                         "undercloud host: {0}".format(self.host))
        sftp = remote_client.open_sftp()
        logger.debug("Downloading \"{0}\"...".format(reportname))
        sftp.get(reportfile, ('{0}/{1}'.format(dl_folder, reportname)))
        logger.debug("Downloading \"{0}\"...".format(resultsname))
        sftp.get(reportfile, ('{0}/{1}'.format(dl_folder, resultsname)))
        sftp.close()
        transport.close()
