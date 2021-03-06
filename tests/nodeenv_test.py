from __future__ import absolute_import
from __future__ import unicode_literals

import os.path
import subprocess

import mock
import pytest

import nodeenv


HERE = os.path.abspath(os.path.dirname(__file__))


@pytest.mark.integration
def test_smoke(tmpdir):
    nenv_path = tmpdir.join('nenv').strpath
    subprocess.check_call([
        # Enable coverage
        'coverage', 'run', '-p',
        '-m', 'nodeenv', '--prebuilt', nenv_path,
    ])
    assert os.path.exists(nenv_path)
    subprocess.check_call([
        'sh', '-c', '. {0}/bin/activate && nodejs --version'.format(nenv_path),
    ])


@pytest.yield_fixture
def mock_index_json():
    # retrieved 2019-12-31
    with open(os.path.join(HERE, 'nodejs_index.json'), 'rb') as f:
        with mock.patch.object(nodeenv, 'urlopen', return_value=f):
            yield


@pytest.yield_fixture
def cap_logging_info():
    with mock.patch.object(nodeenv.logger, 'info') as mck:
        yield mck


def mck_to_out(mck):
    return '\n'.join(call[0][0] for call in mck.call_args_list)


@pytest.mark.usefixtures('mock_index_json')
def test_get_node_versions():
    versions = nodeenv.get_node_versions()
    # there are a lot of versions, just some sanity checks here
    assert len(versions) == 485
    assert versions[:3] == ['0.1.14', '0.1.15', '0.1.16']
    assert versions[-3:] == ['13.3.0', '13.4.0', '13.5.0']


@pytest.mark.usefixtures('mock_index_json')
def test_print_node_versions(cap_logging_info):
    nodeenv.print_node_versions()
    printed = mck_to_out(cap_logging_info)
    assert printed.startswith(
        '0.1.14\t0.1.15\t0.1.16\t0.1.17\t0.1.18\t0.1.19\t0.1.20\t0.1.21\n'
    )
    assert printed.endswith('\n13.1.0\t13.2.0\t13.3.0\t13.4.0\t13.5.0')
    tabs_per_line = [line.count('\t') for line in printed.splitlines()]
    # 8 items per line = 7 tabs
    # The last line contains the remaning 5 items
    assert tabs_per_line == [7] * 60 + [4]


def test_predeactivate_hook(tmpdir):
    # Throw error if the environment directory is not a string
    with pytest.raises((TypeError, AttributeError)):
        nodeenv.set_predeactivate_hook(1)
    # Throw error if environment directory has no bin path
    with pytest.raises((OSError, IOError)):
        nodeenv.set_predeactivate_hook(tmpdir.strpath)
    tmpdir.mkdir('bin')
    nodeenv.set_predeactivate_hook(tmpdir.strpath)
    p = tmpdir.join('bin').join('predeactivate')
    assert 'deactivate_node' in p.read()
