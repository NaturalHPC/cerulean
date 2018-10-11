from cerulean.credential import PasswordCredential, PubKeyCredential
from cerulean.ssh_terminal import SshTerminal


def test_password():
    cred = PasswordCredential('cerulean', 'kingfisher')
    with SshTerminal('cerulean-test-ssh', 22, cred) as term:
        pass


def test_pubkey():
    cred = PubKeyCredential('cerulean', '/home/cerulean/.ssh/id1_rsa')
    with SshTerminal('cerulean-test-ssh', 22, cred) as term:
        pass


def test_passphrase():
    cred = PubKeyCredential(
            'cerulean', '/home/cerulean/.ssh/id2_rsa',
            'kingfisher')
    with SshTerminal('cerulean-test-ssh', 22, cred) as term:
        pass
