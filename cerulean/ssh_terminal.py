import logging
from pathlib import Path
import socket
from time import perf_counter
from types import TracebackType
from typing import Any, List, Optional, Tuple, Type, Union

import paramiko
from cerulean.credential import (Credential, PasswordCredential,
                                 PubKeyCredential)
from cerulean.terminal import Terminal


logger = logging.getLogger(__name__)


class SshTerminal(Terminal):
    """A terminal that runs commands over SSH.

    This terminal connects to a host using SSH, then lets you run commands there.
    """
    def __init__(self, host: str, port: int, credential: Credential) -> None:
        """Create an SshTerminal.

        Arguments:
            host: The hostname to connect to.
            port: The port to connect on.
            credential: The credential to authenticate with.
        """
        self.__host = host
        self.__port = port
        self.__credential = credential

        self.__transport = self.__ensure_connection(None)
        self.__transport2 = None    # type: Optional[paramiko.Transport]

    def __enter__(self) -> 'SshTerminal':
        """Enter context manager."""
        return self

    def __exit__(
            self, exc_type: Optional[Type[BaseException]],
            exc_value: Optional[BaseException],
            traceback: Optional[TracebackType]) -> None:
        """Exit context manager."""
        self.close()

    def close(self) -> None:
        """Close the terminal.

        This closes any connections and frees resources associated with the terminal.
        """
        self.__transport.close()
        logger.debug('Disconnected from SSH server')

    def __eq__(self, other: Any) -> bool:
        """Returns True iff this terminal equals other."""
        if not isinstance(other, Terminal):
            return NotImplemented
        if isinstance(other, SshTerminal):
            return self.__host == other.__host and self.__port == other.__port
        else:
            return False

    def _get_sftp_client(self) -> paramiko.SFTPClient:
        """Get an SFTP client using this terminal.

        This function is used by SftpFileSystem to get an SFTP client using this
        Terminal's connection. This is a private function, but SftpFileSystem is a
        friend class.

        Returns:
            An SFTP client object using this terminal's connection.

        """
        tries = 0
        while tries < 3:
            try:
                self.__transport = self.__ensure_connection(self.__transport)
                client = paramiko.SFTPClient.from_transport(self.__transport)
                break
            except paramiko.ssh_exception.SSHException as e:
                tries += 1

        if client is None:
            raise RuntimeError('Could not open a channel for SFTP')
        return client

    def _get_downstream_sftp_client(self) -> paramiko.SFTPClient:
        """Gets a second SFTP client using this terminal.

        This is a work-around for an issue in paramiko that keeps us from copying data
        upstream and downstream simultaneously through a single connection with
        reasonable performance. We solve it by opening a second connection for the
        downstream part.

        Returns:
            An SFTP client object using a second connection.

        """
        self.__transport2 = self.__ensure_connection(self.__transport2)
        client = paramiko.SFTPClient.from_transport(self.__transport2)
        if client is None:
            raise RuntimeError('Could not open a channel for SFTP')
        return client

    def run(
            self, timeout: float, command: Union[str, Path], args: List[str],
            stdin_data: Optional[str] = None, workdir: Optional[Union[str, Path]] = None
            ) -> Tuple[Optional[int], str, str]:

        if workdir:
            cmd_str = 'cd {}; {} {}'.format(workdir, command, ' '.join(args))
        else:
            cmd_str = '{} {}'.format(command, ' '.join(args))

        logger.debug('Executing %s', cmd_str)
        last_exception = None  # type: Optional[BaseException]
        start_time = perf_counter()
        while perf_counter() < start_time + timeout:
            self.__transport = self.__ensure_connection(self.__transport)
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
                logger.debug(
                        'got output %s %s %s %s', got_all_stdout, stdout_text,
                        got_all_stderr, stderr_text)
                if not got_all_stdout or not got_all_stderr:
                    logger.debug('Command did not finish within timeout')
                    session.close()
                    return None, stdout_text, stderr_text

                session.settimeout(2.0)
                exit_status = session.recv_exit_status()
                logger.debug('received exit status %s', exit_status)
                session.close()

                if exit_status == -1:
                    raise EOFError('Execution failed, connection or server issue?')

                logger.debug('Command executed successfully')
                return exit_status, stdout_text, stderr_text
            except paramiko.SSHException as e:
                last_exception = e
            except EOFError as e:
                last_exception = e
            except ConnectionError as e:
                last_exception = e
            except OSError as e:
                if 'Socket' in str(e):
                    self.__ensure_connection(self.__transport, True)
                last_exception = e

        raise ConnectionError(str(last_exception))

    def __get_data_from_channel(
            self, channel: paramiko.Channel, stream_name: str, timeout: float
            ) -> Tuple[bool, str]:
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
        except ConnectionError:
            return False, data.decode('utf-8')

        return True, data.decode('utf-8')

    def __get_key_from_file(
            self, filename: str, passphrase: Optional[str]) -> paramiko.pkey.PKey:
        key: Optional[paramiko.pkey.PKey] = None
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
            logger.debug('Invalid key: %s', messages)
            raise RuntimeError(
                'Invalid key specified, could not open as RSA, ECDSA or Ed25519 key')

        return key

    def __ensure_connection(
            self, transport: Optional[paramiko.Transport], force: bool = False
            ) -> paramiko.Transport:
        if transport is None or not transport.is_active() or force:
            if transport is not None:
                transport.close()
            transport = paramiko.Transport((self.__host, self.__port))
            logger.info(
                    'Connecting to %s on port %s', self.__host, self.__port)
            try:
                if isinstance(self.__credential, PasswordCredential):
                    logger.debug('Authenticating using a password')
                    transport.connect(
                        username=self.__credential.username,
                        password=self.__credential.password)
                elif isinstance(self.__credential, PubKeyCredential):
                    logger.debug('Authenticating using a public key')
                    key = self.__get_key_from_file(self.__credential.public_key,
                                                   self.__credential.passphrase)
                    transport.connect(username=self.__credential.username, pkey=key)
                else:
                    raise RuntimeError('Unknown kind of credential')
                logger.info('Connection (re)established')
            except paramiko.SSHException:
                raise ConnectionError(
                        'Cerulean was disconnected and could not reconnect')
        return transport
