import os
from os.path import dirname, normpath
from contextlib import contextmanager
import pytest
import dwenv


configs_path = f'{dirname(__file__)}/configs'
os.environ['CONFIGS_ROOT'] = configs_path
start_env = os.environ.copy()


@contextmanager
def preserve_env():
    yield
    os.environ = start_env.copy()


def test_conform_configs_paths_var():
    #
    paths = dwenv.env.conform_configs_paths_var(
        f'{configs_path}/test_env1.env')
    assert isinstance(paths, list)
    assert len(paths) == 1
    assert normpath(paths[0]) == normpath('${CONFIGS_ROOT}/cfg1.envc')
    #
    paths = dwenv.env.conform_configs_paths_var(
        f'{configs_path}/cfg1.envc')
    assert isinstance(paths, list)
    assert len(paths) == 1
    assert normpath(paths[0]) == normpath(f'{configs_path}/cfg1.envc')
    #
    paths = dwenv.env.conform_configs_paths_var(
        [f'{configs_path}/cfg1.envc'])
    assert isinstance(paths, list)
    assert len(paths) == 1
    assert normpath(paths[0]) == normpath(f'{configs_path}/cfg1.envc')


@preserve_env()
@pytest.mark.parametrize('config', [
        f'{configs_path}/test_env1.env',
        f'{configs_path}/cfg1.envc',
        [f'{configs_path}/cfg1.envc'],
    ])
def test_set_append_prepend(config):
    var, value = 'NEW_VAR', 'test'
    assert var not in start_env
    env = dwenv.build_env(config)
    assert env[var] == value
    assert env['PATH'].endswith('appended')
    assert env['PATH'].startswith('prepended')


@preserve_env()
@pytest.mark.parametrize('target_platform', [None, 'windows', 'linux'])
def test_not_from_current_env(target_platform):
    random_var = list(os.environ.keys())[0]
    assert random_var != 'NEW_VAR'
    env = dwenv.build_env(
        f'{configs_path}/test_env1.env', from_current_env=False,
        target_platform=target_platform)
    assert env['NEW_VAR'] == 'test'
    assert env['PATH'].endswith('appended')
    assert env['PATH'].startswith('prepended')
    assert random_var not in env


@preserve_env()
def test_remove_key():
    var, value = 'SOME_ENV', 'abc'
    os.environ[var] = value
    env = dwenv.build_env(f'{configs_path}/test_env1.env')
    assert env[var] == value
    env = dwenv.build_env(
        f'{configs_path}/test_env1.env', vars_to_remove=[var])
    assert var not in env
