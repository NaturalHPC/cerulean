import socket
from types import TracebackType
from typing import cast, List, Optional, Tuple, Type, TYPE_CHECKING

import paramiko
from cerulean.credential import (Credential, PasswordCredential,
                                 PubKeyCredential)
from cerulean.terminal import Terminal
from cerulean.util import BaseExceptionType


class SshTerminal(Terminal):
    def __init__(self, host: str, port: int, credential: Credential) -> None:
        self.__transport = paramiko.Transport((host, port))
        if isinstance(credential, PasswordCredential):
            self.__transport.connect(
                username=credential.username, password=credential.password)
        elif isinstance(credential, PubKeyCredential):
            key = self.__get_key_from_file(credential.public_key,
                                           credential.passphrase)
            self.__transport.connect(username=credential.username, pkey=key)
        else:
            raise RuntimeError('Unknown kind of certificate')

    def __enter__(self) -> 'SshTerminal':
        return self

    def __exit__(self, exc_type: Optional[BaseExceptionType],
                 exc_value: Optional[BaseException],
                 traceback: Optional[TracebackType]) -> None:
        self.__transport.close()

    def _get_sftp_client(self) -> paramiko.SFTPClient:
        """Get an SFTP client using this terminal.

        This function is used by SftpFileSystem to get an SFTP client \
        using this Terminal's connection. This is a private function, \
        but SftpFileSystem is a friend class.

        Returns:
            An SFTP client object using this terminal's connection.
        """
        return paramiko.SFTPClient.from_transport(self.__transport)

    def run(self,
            timeout: float,
            command: str,
            args: List[str],
            stdin_data: str = None,
            workdir: str = None) -> Tuple[Optional[int], str, str]:

        if workdir:
            cmd_str = 'cd {}; {} {}'.format(workdir, command, ' '.join(args))
        else:
            cmd_str = '{} {}'.format(command, ' '.join(args))

        session = self.__transport.open_session()
        session.exec_command(command=cmd_str)
        if stdin_data is not None:
            session.sendall(bytes(stdin_data, 'utf-8'))
            session.shutdown_write()

        got_all_stdout, stdout_text = self.__get_data_from_channel(
            session, 'stdout', timeout)
        got_all_stderr, stderr_text = self.__get_data_from_channel(
            session, 'stderr', timeout)
        if not got_all_stdout or not got_all_stderr:
            return None, stdout_text, stderr_text

        session.settimeout(2.0)
        exit_status = session.recv_exit_status()
        session.close()

        return exit_status, stdout_text, stderr_text

    def __get_data_from_channel(self, channel: paramiko.Channel,
                                stream_name: str,
                                timeout: float) -> Tuple[bool, str]:
        """Reads text from standard output or standard error."""
        if stream_name == 'stdout':
            receive = paramiko.Channel.recv
        else:
            receive = paramiko.Channel.recv_stderr

        channel.settimeout(timeout)

        data = bytearray()
        try:
            new_data = receive(channel, 1024 * 1024)
            while len(new_data) > 0:
                data.extend(new_data)
                new_data = receive(channel, 1024 * 1024)
        except socket.timeout:
            return False, data.decode('utf-8')

        return True, data.decode('utf-8')

    def __get_key_from_file(self, filename: str,
                            passphrase: Optional[str]) -> paramiko.pkey.PKey:
        key = None
        try:
            key = paramiko.ed25519key.Ed25519Key.from_private_key_file(
                filename=filename, password=passphrase)
        except paramiko.ssh_exception.SSHException:
            key = None

        if key is None:
            try:
                key = paramiko.ecdsakey.ECDSAKey.from_private_key_file(
                    filename=filename, password=passphrase)
            except paramiko.ssh_exception.SSHException:
                key = None

        if key is None:
            try:
                key = paramiko.rsakey.RSAKey.from_private_key_file(
                    filename=filename, password=passphrase)
            except paramiko.ssh_exception.SSHException:
                key = None

        if key is None:
            raise RuntimeError(
                'Invalid key specified, could not open as RSA, ECDSA or Ed25519 key'
            )

        return key
