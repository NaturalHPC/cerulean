import errno
import logging
import stat
from pathlib import PurePosixPath
import requests
from urllib.parse import urljoin, urlparse
from types import TracebackType
from typing import Any, cast, Dict, Generator, Iterable, List, Optional, Tuple
from xml.etree.ElementTree import Element

import defusedxml.ElementTree as ET     # type: ignore

from cerulean.credential import Credential, PasswordCredential
from cerulean.file_system import FileSystem, UnsupportedOperationError
from cerulean.file_system_impl import FileSystemImpl
from cerulean.path import AbstractPath, EntryType, Path, Permission
from cerulean.util import BaseExceptionType


logger = logging.getLogger(__name__)


class WebdavFileSystem(FileSystemImpl):
    """A FileSystem implementation that connects to a WebDAV server.

    WebdavFileSystem supports the / operation:

    .. code-block:: python

      fs / 'path'

    which produces a :class:`Path`, through which you can do things \
    with the remote files.

    It is also a context manager, so that you can (and should!) use it \
    with a ``with`` statement, which will ensure that the connection \
    is closed when you are done with the it. Alternatively, you can \
    call :meth:`close` to close the connection.

    The WebDAV protocol does not support all operations specified by \
    the Cerulean API. In particular, symbolic links are not supported, \
    nor are ownership and permissions. Read-access to these properties \
    is emulated, e.g. `is_symlink()` simply always returns false, all \
    files and directories are owned by uid 0 and gid 0, with access \
    permissions determined by whether the server will let us access \
    them.

    By default, if you try to run any of the related modifying methods, \
    e.g. `symlink_to()` or `set_permissions()`, an \
    :class:`UnsupportedOperationError` will be raised. If you set \
    `unsupported_methods_raise` to `False` when creating a \
    WebdavFileSystem, then these methods will simply return without \
    doing anything.

    WebdavFileSystem supports both HTTP and HTTPS, but not (yet) \
    client-side certificates.

    Args:
        url: The server base location, e.g. http://example.com/webdav
        credential: The credential to use to connect.
        host_ca_cert_file: Path to a certificate file to use for \
                authentication. Useful for servers that use a self-signed \
                certificate.
        unsupported_methods_raise: Raise on using an unsupported \
                method, see above.
    """
    def __init__(self, url: str,
                 credential: Optional[Credential] = None,
                 host_ca_cert_file: Optional[str] = None,
                 unsupported_methods_raise: Optional[bool] = True) -> None:
        self.__base_url = url.rstrip('/')
        self.__credential = credential
        self.__host_ca_cert_file = host_ca_cert_file
        self.__unsupported_methods_raise = unsupported_methods_raise
        self.__ensure_http(True)
        self.__max_tries = 3

    def __enter__(self) -> 'WebdavFileSystem':
        return self

    def __exit__(self, exc_type: Optional[BaseExceptionType],
                 exc_value: Optional[BaseException],
                 traceback: Optional[TracebackType]) -> None:
        self.close()

    def close(self) -> None:
        self.__session.close()
        logger.info('Disconnected from WebDAV server')

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, FileSystem):
            return NotImplemented
        if isinstance(other, WebdavFileSystem):
           return self.__base_url == other.__base_url
        else:
            return False

    def root(self) -> Path:
        return Path(self, PurePosixPath('/'))

    def __truediv__(self, segment: str) -> Path:
        return Path(self, PurePosixPath('/' + segment.strip('/')))

    def _supports(self, feature: str) -> bool:
        if feature not in self._features:
            raise ValueError('Invalid argument for "feature"')
        # supports symlinks nor permissions nor devices
        return False

    def _exists(self, path: AbstractPath) -> bool:
        self.__ensure_http()
        response = self.__session.head(self.__url(path))
        return response.status_code == 200

    def _mkdir(self,
              path: AbstractPath,
              mode: Optional[int] = None,
              parents: bool = False,
              exists_ok: bool = False) -> None:

        def handle_mkcol_error(response: requests.Response) -> None:
            if response.status_code == 201:
                pass
            elif response.status_code == 403:
                raise PermissionError(('Permission denied while accessing {}'
                                      ).format(self.__url(path)))
            elif response.status_code == 405:
                raise FileExistsError(('File or directory {} already exists'
                                      ).format(self.__url(path)))
            elif response.status_code == 409:
                raise FileNotFoundError(('One or more parent directories of'
                                         ' {} do not exist').format(
                                             self.__url(path)))
            elif response.status_code == 507:
                raise IOError(('Out of storage space while making dir {}'
                              ).format(self.__url(path)))
            else:
                raise RuntimeError(('An error occurred while making'
                                    ' dir {}, the server said {}').format(
                                        self.__url(path), response.reason))

        if mode is not None and self.__unsupported_methods_raise:
            raise UnsupportedOperationError('Tried to make a directory with a'
                                            ' permission mask, but WebDAV does'
                                            ' not support permissions.')
        self.__ensure_http()
        lpath = cast(PurePosixPath, path)
        if parents:
            for parent in reversed(lpath.parents):
                if not self._exists(parent):
                    response = self.__session.request('MKCOL',
                                                      self.__url(parent))
                    handle_mkcol_error(response)
        if self._exists(lpath):
            if not exists_ok:
                raise FileExistsError(
                    'File {} exists and exists_ok was False'.format(lpath))
            else:
                return

        response = self.__session.request('MKCOL', self.__url(lpath))
        handle_mkcol_error(response)

    def _iterdir(self, path: AbstractPath) -> Generator[PurePosixPath, None, None]:
        self.__ensure_http()
        url = self.__url(path)
        collection = self.__propfind(url, None, 1)
        for child_url in collection.keys():
            child_abs_url = urljoin(self.__base_url, child_url)
            if child_abs_url != url:
                if not child_abs_url.startswith(self.__base_url):
                    raise RuntimeError(('Something went wrong processing a'
                                        ' URL returned by the WebDAV server'
                                        ' in iterdir(). The URL is {} and'
                                        ' the base URL is {}.').format(
                                            child_url, self.__base_url))
                rel_child_path = child_abs_url[len(self.__base_url):]
                rel_child = PurePosixPath(rel_child_path)
                if self._exists(rel_child):
                    yield rel_child

    def _rmdir(self, path: AbstractPath, recursive: bool = False) -> None:
        self.__ensure_http()
        url = self.__url(path)
        if not self._exists(path):
            return

        if not self._is_dir(path):
            raise RuntimeError("Path must refer to a directory")

        props = self.__propfind(url, None, 1)
        if not recursive and len(props) > 1:
            raise OSError(errno.ENOTEMPTY, 'Directory not empty', url)

        self.__session.delete(url)

    def _touch(self, path: AbstractPath) -> None:
        self.__ensure_http()
        url = self.__url(path)
        if not self._exists(path):
            response = self.__session.put(url, bytes())
            if response.status_code < 400 or response.status_code == 409:
                # we ignore 409 Conflict, since that means that a resource
                # exists at this point, which is what we're trying to achieve
                pass
            else:
                raise RuntimeError(('Error trying to create file {}: {}'
                                   ).format(url, response.reason))

    def _streaming_read(self, path: AbstractPath) -> Generator[bytes, None, None]:
        self.__ensure_http()
        url = self.__url(path)

        with self.__session.get(url, stream=True) as response:
            yield from response.iter_content(24576)

    def _streaming_write(self, path: AbstractPath, data: Iterable[bytes]) -> None:
        def data_generator(data: Iterable[bytes]) -> Generator[bytes, None, None]:
            for chunk in data:
                yield chunk

        self.__ensure_http()
        url = self.__url(path)
        self.__session.put(url, data=data_generator(data))    # type: ignore

    def _rename(self, path: AbstractPath, target: AbstractPath) -> None:
        self.__ensure_http()
        url = self.__url(path)
        target_url = self.__url(target)
        headers = {
                'Destination': target_url,
                'Overwrite': 'T'
                }
        response = self.__session.request('MOVE', url, headers=headers)
        if response.status_code in [201, 204]:
            pass
        else:
            raise RuntimeError(('An error occurred while moving'
                                ' {}, the server said {}').format(
                                    url, response.reason))

    def _unlink(self, path: AbstractPath) -> None:
        self.__ensure_http()
        if not self._is_file(path):
            raise IsADirectoryError(errno.EISDIR, 'Is a directory', str(path))

        url = self.__url(path)
        response = self.__session.delete(url)
        if response.status_code != 204:
            raise RuntimeError(('An error occurred when deleting'
                                ' file {}, the server said {}').format(
                                    self.__url(path), response.reason))


    def _is_dir(self, path: AbstractPath) -> bool:
        self.__ensure_http()
        if not self._exists(path):
            return False

        url = self.__url(path)
        props = self.__propfind(url, '{DAV:}resourcetype')
        if props[url] is None:
            return False
        return props[url].find('{DAV:}collection') is not None

    def _is_file(self, path: AbstractPath) -> bool:
        self.__ensure_http()
        if not self._exists(path):
            return False

        return not self._is_dir(path)

    def _is_symlink(self, path: AbstractPath) -> bool:
        return False

    def _entry_type(self, path: AbstractPath) -> EntryType:
        if not self._exists(path):
            raise OSError(errno.ENOENT, 'No such file or directory', path)
        if self._is_dir(path):
            return EntryType.DIRECTORY
        else:
            return EntryType.FILE

    def _size(self, path: AbstractPath) -> int:
        self.__ensure_http()
        url = self.__url(path)
        props = self.__propfind(url, '{DAV:}getcontentlength')
        return int(''.join(props[url].itertext()))

    def _uid(self, path: AbstractPath) -> int:
        return 0

    def _gid(self, path: AbstractPath) -> int:
        return 0

    def _has_permission(self, path: AbstractPath, permission: Permission
                        ) -> bool:
        permissions = [Permission.OWNER_READ, Permission.OWNER_WRITE]
        if self._is_dir(path):
            permissions.append(Permission.OWNER_EXECUTE)
        return permission in permissions

    def _set_permission(self,
                       path: AbstractPath,
                       permission: Permission,
                       value: bool = True) -> None:
        if self.__unsupported_methods_raise:
            raise UnsupportedOperationError(
                    'WebDAV does not support Posix permissions')

    def _chmod(self, path: AbstractPath, mode: int) -> None:
        if self.__unsupported_methods_raise:
            raise UnsupportedOperationError(
                    'WebDAV does not support Posix permissions')

    def _symlink_to(self, path: AbstractPath, target: AbstractPath) -> None:
        if self.__unsupported_methods_raise:
            raise UnsupportedOperationError(
                    'WebDAV does not support symbolic links')

    def _readlink(self, path: AbstractPath, recursive: bool) -> Path:
        url = self.__url(path)
        raise OSError(errno.EINVAL, 'Invalid argument', url)

    def __ensure_http(self, first: bool = False) -> None:
        # Note: first can be removed, session will do all this stuff
        # automatically if the connection was closed and we make another
        # request on the session.
        if first:
            logger.info('Connecting to WebDAV server')
            self.__session = requests.Session()
            if self.__credential is not None:
                if isinstance(self.__credential, PasswordCredential):
                    self.__session.auth = (
                            self.__credential.username,
                            self.__credential.password)
                else:
                    raise ValueError('Only a PasswordCredential can be used'
                                     ' with WebdavFileSystem.')
            if self.__host_ca_cert_file is not None:
                if isinstance(self.__host_ca_cert_file, str):
                    self.__session.verify = self.__host_ca_cert_file
            response = self.__session.head(self.__base_url)
            if response.status_code != 200:
                raise RuntimeError('Error connecting to WebDAV server at {}:'
                                   ' {}'.format(self.__base_url,
                                       response.reason))
            logger.info('Connected to WebDAV server')

    def __url(self, path: AbstractPath) -> str:
        return self.__base_url + str(path)

    def __propfind(self, url: str, req_prop: Optional[str], depth: int = 0
                   ) -> Dict[str, Element]:
        """Runs a PROPFIND command for a given resource.

        Actually, just requests everything and searches the result.

        Args:
            url: The url to query.
            req_prop: The property to request.
            depth: Depth to recurse to, either 0 or 1.

        Returns:
            A dictionary mapping urls to XML subtrees.
        """
        headers = { 'Depth': str(depth) }
        response = self.__session.request('PROPFIND', url, headers=headers)
        if response.status_code < 400:
            print(response.text)
            xml_props = ET.fromstring(response.text)
            results = dict()
            for resp in xml_props.iter('{DAV:}response'):
                prop_url = resp.findtext('{DAV:}href')
                prop_url = urljoin(self.__base_url, prop_url)
                propstat = resp.find('{DAV:}propstat')
                prop = propstat.find('{DAV:}prop')
                if req_prop is not None:
                    results[prop_url] = prop.find(req_prop)
                else:
                    results[prop_url] = None
            return results
        elif response.status_code == 401:
            raise PermissionError('Invalid credentials supplied')
        elif response.status_code == 403:
            raise PermissionError(('Permission denied while accessing {}'
                                  ).format(url))
        else:
            raise RuntimeError(('An error occurred while checking dir {},'
                                ' the server said {}').format(url,
                                    response.reason))
