def test_joinpath(paths):
    new_path = paths['root'].joinpath('links')
    assert paths['dir'] == new_path


def test_with_name(local_filesystem):
    new_path = (local_filesystem / 'home').with_name('usr')
    assert str(new_path) == '/usr'


def test_with_suffix(local_filesystem):
    new_path = (local_filesystem / 'test.txt').with_suffix('.dat')
    assert str(new_path) == '/test.dat'


def test_read_bytes(paths):
    data = paths['file'].read_bytes()
    assert data.decode('utf-8') == 'Hello World\n'
