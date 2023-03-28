__copyright__ = 'DreamWall'
__author__ = 'Olivier Evers'
__license__ = 'MIT'


import os
import re
import json
from platform import system


PLATFORM = system().lower()
COMMENT_SYMBOLS = '#', '//'


def expand_variables(path, env):
    path = os.path.expanduser(path)
    for k, v in env.items():
        path = path.replace('${%s}' % k, v)
    return path


def get_separator(platform=PLATFORM):
    if platform == 'windows':
        return ';'
    else:
        return ':'


def get_start_env(
        start_env='current',
        vars_to_remove=None,
        initial_vars=None,
        start_env_backup_path=None):

    if start_env == 'current':
        env = os.environ.copy()
    elif isinstance(start_env, dict):
        env = start_env
    elif isinstance(start_env, str):
        with open(os.path.expandvars(start_env), 'r') as f:
            env = json.load(f)
    else:
        env = {}

    if start_env_backup_path:
        with open(os.path.expandvars(start_env_backup_path), 'w') as f:
            json.dump(env, f)

    if vars_to_remove:
        for var in vars_to_remove:
            env.pop(var, None)

    if initial_vars:
        env = {var: os.environ[var] for var in initial_vars}

    return env


def _expand_and_check_exists(config_path):
    config_path = os.path.expandvars(config_path)
    if not os.path.exists(config_path):
        raise FileNotFoundError(f'Config file missing: {config_path}')
    return config_path


def conform_configs_paths_var(configs_paths):
    """
    returns list of .envc files.
    if configs_paths is a single .env file, it will return its content.
    if it's is a single .envc file, it will return it as a single item list.
    """
    if isinstance(configs_paths, (list, set, tuple)):
        return [_expand_and_check_exists(p) for p in configs_paths if p]
    elif configs_paths.endswith('.envc'):
        configs_paths = _expand_and_check_exists(configs_paths)
        return [configs_paths]
    elif configs_paths.endswith('.env'):
        configs_paths = _expand_and_check_exists(configs_paths)
        with open(configs_paths, 'r') as f:
            return [
                _expand_and_check_exists(ln.strip()) for ln in f.readlines() if
                ln.strip() and
                not ln.startswith(COMMENT_SYMBOLS)]
    else:
        raise ValueError('Wrong extension for configs_paths')


def print_env(env, separator=None):  # pragma: no cover
    separator = separator or get_separator()
    for var in sorted(env.keys()):
        print('\n' + var)
        for path in env[var].split(separator):
            print(' - ' + path)


def extend_env_with_envconfig(
        env, target_platform, config_path, override_warnings=True):

    separator = get_separator(target_platform)

    with open(config_path, 'r') as config:
        for line in config:
            line = line.strip()
            if not line:
                continue
            if line.startswith(COMMENT_SYMBOLS):
                continue

            # Parse for variable, operator, (platform) and value
            try:
                variable, operator, value = re.split(
                    r'(\s=\s|\s>\s|\s<\s)', line)
            except ValueError:
                raise ValueError(f'Wrong input in config: {line}')
            try:
                variable, var_platform = re.split(r'\.', variable)
            except ValueError:
                var_platform = None

            # Skip values for other platforms:
            if not (target_platform == var_platform or var_platform is None):
                continue

            # Inject variable
            value = expand_variables(value, env)
            if operator == ' = ':
                if override_warnings and variable in env:
                    print(
                        f'WARNING: "{os.path.basename(config_path)}" '
                        f'replacing existing variable "{variable}".')
                env[variable] = value
            else:
                # Check that variable exists:
                if variable not in env:
                    env[variable] = value
                    continue
                # Check that value doesn't exist:
                elif value in env[variable].split(separator):
                    continue
                # Append or prepend value:
                if operator == ' > ':
                    env[variable] += separator + value
                elif operator == ' < ':
                    env[variable] = value + separator + env[variable]


def build_env(
        configs_paths=None,
        start_env='current',
        vars_to_remove=None,
        initial_vars=None,
        override_warnings=True,
        target_platform=None,
        start_env_backup_path=None,
        set_current_env=False,
        verbose=False):
    """
    configs_path: you can pass a single .env config path or a list of .envc's
    """
    target_platform = target_platform or PLATFORM
    separator = get_separator(target_platform)
    env = get_start_env(
        start_env, vars_to_remove, initial_vars, start_env_backup_path)

    if configs_paths is None:
        # Use DWENV_CONFIG value if no configs_paths provided:
        configs_paths = os.environ['DWENV_CONFIG']
    elif isinstance(configs_paths, str):
        env['DWENV_CONFIG'] = configs_paths

    configs_paths = conform_configs_paths_var(configs_paths)

    # Build from configs:
    for config_path in configs_paths:
        extend_env_with_envconfig(
            env, target_platform, config_path, override_warnings)

    # Force string type
    env = {str(k): str(v) for k, v in env.items()}

    if set_current_env:
        os.environ.clear()
        os.environ.update(env)

    if verbose:  # pragma: no cover
        print_env(env, separator)

    return env
