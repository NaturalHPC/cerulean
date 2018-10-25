import logging
import socket
from time import perf_counter
from types import TracebackType
from typing import List, Optional, Tuple, Type, TYPE_CHECKING

import paramiko
from cerulean.credential import (Credential, PasswordCredential,
                                 PubKeyCredential)
from cerulean.terminal import Terminal
from cerulean.util import BaseExceptionType


logger = logging.getLogger(__name__)


class SshTerminal(Terminal):
    """A terminal that runs commands over SSH.

    This terminal connects to a host using SSH, then lets you run \
    commands there.

    Arguments:
        host: The hostname to connect to.
        port: The port to connect on.
        credential: The credential to authenticate with.
    """
    def __init__(self, host: str, port: int, credential: Credential) -> None:
        self.__host = host
        self.__port = port
        self.__credential = credential

        self.__transport = paramiko.Transport((host, port))
        self.__ensure_connection()

    def __enter__(self) -> 'SshTerminal':
        return self

    def __exit__(self, exc_type: Optional[BaseExceptionType],
                 exc_value: Optional[BaseException],
                 traceback: Optional[TracebackType]) -> None:
        self.close()

    def close(self) -> None:
        """Close the terminal.

        This closes any connections and frees resources associated \
        with the terminal.
        """
        self.__transport.close()
        logger.debug('Disconnected from SSH server')

    def _get_sftp_client(self) -> paramiko.SFTPClient:
        """Get an SFTP client using this terminal.

        This function is used by SftpFileSystem to get an SFTP client \
        using this Terminal's connection. This is a private function, \
        but SftpFileSystem is a friend class.

        Returns:
            An SFTP client object using this terminal's connection.
        """
        self.__ensure_connection()
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

        logger.debug('Executing {}'.format(cmd_str))
        last_exception = None  # type: Optional[BaseException]
        start_time = perf_counter()
        while perf_counter() < start_time + timeout:
            self.__ensure_connection()
            try:
                session = self.__transport.open_session()
                logger.debug('Opened session')
                session.exec_command(command=cmd_str)
                logger.debug('exec_command done')
                if stdin_data is not None:
                    session.sendall(bytes(stdin_data, 'utf-8'))
                    session.shutdown_write()
                logger.debug('stdin sent')

                got_all_stdout, stdout_text = self.__get_data_from_channel(
                    session, 'stdout', timeout)
                got_all_stderr, stderr_text = self.__get_data_from_channel(
                    session, 'stderr', timeout)
                logger.debug('got output {} {} {} {}'.format(
                        got_all_stdout, stdout_text, got_all_stderr, stderr_text))
                if not got_all_stdout or not got_all_stderr:
                    logger.debug('Command did not finish within timeout')
                    session.close()
                    return None, stdout_text, stderr_text

                session.settimeout(2.0)
                exit_status = session.recv_exit_status()
                logger.debug('received exit status {}'.format(exit_status))
                session.close()

                if exit_status == -1:
                    raise EOFError('Execution failed, connection'
                                   ' or server issue?')

                logger.debug('Command executed successfully')
                return exit_status, stdout_text, stderr_text
            except paramiko.SSHException as e:
                last_exception = e
            except EOFError as e:
                last_exception = e
            except ConnectionError as e:
                last_exception = e

        raise ConnectionError(str(last_exception))

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
        messages = ''
        try:
            key = paramiko.ed25519key.Ed25519Key.from_private_key_file(
                filename=filename, password=passphrase)
        except paramiko.ssh_exception.SSHException as e:
            key = None
            messages += '{}; '.format(e)

        if key is None:
            try:
                key = paramiko.ecdsakey.ECDSAKey.from_private_key_file(
                    filename=filename, password=passphrase)
            except paramiko.ssh_exception.SSHException as e:
                key = None
                messages += '{}; '.format(e)

        if key is None:
            try:
                key = paramiko.rsakey.RSAKey.from_private_key_file(
                    filename=filename, password=passphrase)
            except paramiko.ssh_exception.SSHException as e:
                key = None
                messages += '{}; '.format(e)

        if key is None:
            logger.debug('Invalid key: {}'.format(messages))
            raise RuntimeError(
                'Invalid key specified, could not open as RSA, ECDSA or Ed25519 key'
            )

        return key

    def __ensure_connection(self) -> None:
        if not self.__transport.is_active():
            self.__transport.close()
            self.__transport = paramiko.Transport((self.__host, self.__port))
            logger.info('Connecting to {} on port {}'.format(self.__host, self.__port))
            try:
                if isinstance(self.__credential, PasswordCredential):
                    logger.debug('Authenticating using a password')
                    self.__transport.connect(
                        username=self.__credential.username,
                        password=self.__credential.password)
                elif isinstance(self.__credential, PubKeyCredential):
                    logger.debug('Authenticating using a public key')
                    key = self.__get_key_from_file(self.__credential.public_key,
                                                   self.__credential.passphrase)
                    self.__transport.connect(username=self.__credential.username, pkey=key)
                else:
                    raise RuntimeError('Unknown kind of credential')
                logger.info('Connection (re)established')
            except paramiko.SSHException:
                raise ConnectionError('Cerulean was disconnected and could not reconnect')
