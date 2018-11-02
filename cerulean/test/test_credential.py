import pytest
from cerulean import PasswordCredential, PubKeyCredential


def test_password_credential() -> None:
    cred = PasswordCredential('cerulean', 'kingfisher')

    assert cred.username == 'cerulean'
    assert cred.password == 'kingfisher'


def test_pubkey_credential() -> None:
    cred = PubKeyCredential('cerulean', '/home/cerulean/.ssh/id1_rsa')

    assert cred.username == 'cerulean'
    assert cred.public_key == '/home/cerulean/.ssh/id1_rsa'
    assert cred.passphrase is None


def test_pubkey_passphrase_credential() -> None:
    cred = PubKeyCredential('cerulean', '/home/cerulean/.ssh/id2_rsa', 'kingfisher')

    assert cred.username == 'cerulean'
    assert cred.public_key == '/home/cerulean/.ssh/id2_rsa'
    assert cred.passphrase == 'kingfisher'
