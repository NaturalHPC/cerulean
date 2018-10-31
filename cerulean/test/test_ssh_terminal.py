from cerulean import PasswordCredential, PubKeyCredential
from cerulean import SshTerminal


def test_password() -> None:
    cred = PasswordCredential('cerulean', 'kingfisher')
    with SshTerminal('cerulean-test-ssh', 22, cred) as term:
        pass


def test_pubkey() -> None:
    cred = PubKeyCredential('cerulean', '/home/cerulean/.ssh/id1_rsa')
    with SshTerminal('cerulean-test-ssh', 22, cred) as term:
        pass


def test_passphrase() -> None:
    cred = PubKeyCredential(
            'cerulean', '/home/cerulean/.ssh/id2_rsa',
            'kingfisher')
    with SshTerminal('cerulean-test-ssh', 22, cred) as term:
        pass
