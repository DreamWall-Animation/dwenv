import os
from os.path import dirname, normpath
from contextlib import contextmanager
import pytest
import dwenv


configs_path = f'{dirname(__file__)}/configs'
os.environ['CONFIGS_ROOT'] = configs_path
start_env = os.environ.copy()


@contextmanager
def reset_env():
    os.environ = start_env.copy()
    yield


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


@reset_env()
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


def test_use_DWENV_CONFIG():
    var, value = 'NEW_VAR', 'test'
    assert var not in start_env
    os.environ['DWENV_CONFIG'] = f'{configs_path}/test_env1.env'
    env = dwenv.build_env()
    assert env[var] == value
    assert env['PATH'].endswith('appended')
    assert env['PATH'].startswith('prepended')


def test_bad_config_path():
    with pytest.raises(FileNotFoundError, match=r'Config file missing.*'):
        dwenv.build_env('/path/does/not/exist.envc')
    with pytest.raises(ValueError, match=r'Wrong extension.*'):
        dwenv.build_env('/path/with/wrong/extension')


def test_bad_config():
    with pytest.raises(ValueError):
        dwenv.build_env(f'{configs_path}/bad_cfg.envc')


def test_override_warning():
    dwenv.build_env(f'{configs_path}/replace_path.envc')


def test_add_same_value_twice():
    env = dwenv.build_env(
        [f'{configs_path}/cfg1.envc', f'{configs_path}/cfg2.envc'])
    assert env['PATH'].count('appended') == 1


@reset_env()
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
    if target_platform == 'linux':
        assert env['PLATFORMVAR'] == 'linuxvar'
    elif target_platform == 'windows':
        assert env['PLATFORMVAR'] == 'windowsvar'


@reset_env()
def test_remove_key():
    var, value = 'SOME_ENV', 'abc'
    os.environ[var] = value
    env = dwenv.build_env(f'{configs_path}/test_env1.env')
    assert env[var] == value
    env = dwenv.build_env(
        f'{configs_path}/test_env1.env', vars_to_remove=[var])
    assert var not in env


@reset_env()
def test_selected_vars():
    var, value = 'SOME_ENV', 'abc'
    os.environ[var] = value
    env = dwenv.build_env(f'{configs_path}/test_env1.env')
    assert env[var] == value
    env = dwenv.build_env(
        f'{configs_path}/test_env1.env', initial_vars=[var])
    assert len(env) == 5
    assert env[var] == value
