from abc import ABC


class Credential(ABC):
    """A credential for connecting to remote machines.

    Credentials don't have much in common other than a username, \
    which is best modelled as a public attribute. So this interface \
    is empty, and only here to provide a generic type to represent \
    any credential in the API.

    Attributes:
        username: The name of the user to connect as.
    """
    pass


class PasswordCredential(Credential):
    """A credential comprising a username and password.

    Attributes:
        username: The name of the user to connect as
        password: The password to authenticate with
    """

    def __init__(self, username: str, password: str) -> None:
        """Create a PasswordCredential.

        Args:
            username: The name of the user to connect as
            password: The password to authenticate with
        """
        self.username = username
        self.password = password


class PubKeyCredential(Credential):
    """A credential using a public/private key pair.

    Attributes:
        username: The name of the user to connect as
        public_key: The (local) path to a key file
        passphrase: The passphrase to decrypt the key with; optional.
    """

    def __init__(self, username: str, public_key: str,
                 passphrase: str = None) -> None:
        """Create a PubKeyCredential.

        Args:
            username: The name of the user to connect as
            pub_key: The (local) path to a key file
            passphrase The passphrase to decrypt the key with; optional.
        """
        self.username = username
        self.public_key = public_key
        self.passphrase = passphrase
