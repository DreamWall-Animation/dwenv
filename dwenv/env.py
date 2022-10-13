__copyright__ = 'DreamWall'
__author__ = 'Olivier Evers'
__license__ = 'MIT'


import os
import re
import sys
from platform import system


PLATFORM = system().lower()
COMMENT_SYMBOLS = '#', '//'


def expand_variables(path, env):
    for k, v in env.items():
        path = path.replace('${%s}' % k, v)
    return path


def get_separator(platform=PLATFORM):
    if platform == 'windows':
        return ';'
    else:
        return ':'


def get_start_env(
        from_current_env=True,
        start_env=None,
        vars_to_remove=None,
        initial_vars=None):
    if not from_current_env:
        env = start_env or {}
    else:
        env = os.environ.copy()

    if vars_to_remove:
        for var in vars_to_remove:
            env.pop(var, None)

    if initial_vars:
        env = {var: os.environ[var] for var in initial_vars}

    return env


def _check_config_file_exists(config_path):
    if not os.path.exists(config_path):
        raise FileNotFoundError('Config file missing: %s' % config_path)


def conform_configs_paths_var(configs_paths):
    """
    returns list of .envc files.
    if configs_paths is a single .env file, it will return its content.
    if it's is a single .envc file, it will return it as a single item list.
    """
    if isinstance(configs_paths, (list, set, tuple)):
        [_check_config_file_exists(p) for p in configs_paths if p]
        return configs_paths
    elif configs_paths.endswith('.envc'):
        _check_config_file_exists(configs_paths)
        return [configs_paths]
    elif configs_paths.endswith('.env'):
        _check_config_file_exists(configs_paths)
        with open(configs_paths, 'r') as f:
            return [
                l.strip() for l in f.readlines() if l and
                not l.startswith(COMMENT_SYMBOLS)]
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
                raise ValueError('Wrong input in config: %s' % line)
            try:
                variable, var_platform = re.split(r'\.', variable)
            except ValueError:
                var_platform = None

            # Skip values for other platforms:
            if not(target_platform == var_platform or var_platform is None):
                continue

            # Inject variable
            value = expand_variables(value, env)
            if operator == ' = ':
                if override_warnings and variable in env:
                    print('WARNING: "%s" replacing existing variable "%s".' % (
                        os.path.basename(config_path), variable))
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
        from_current_env=True,
        start_env=None,
        vars_to_remove=None,
        initial_vars=None,
        override_warnings=True,
        target_platform=None,
        verbose=False):
    """
    configs_path: you can pass a single .env config path or a list of .envc's
    """
    target_platform = target_platform or PLATFORM
    separator = get_separator(target_platform)
    env = get_start_env(
        from_current_env, start_env, vars_to_remove, initial_vars)

    if configs_paths is None:
        # Use DWENV_CONFIG value if no configs_paths provided:
        configs_paths = os.environ['DWENV_CONFIG']
    elif isinstance(configs_paths, str):
        env['DWENV_CONFIG'] = configs_paths

    configs_paths = conform_configs_paths_var(configs_paths)

    # Build from configs:
    for config_path in configs_paths:
        config_path = os.path.expandvars(config_path)
        extend_env_with_envconfig(
            env, target_platform, config_path, override_warnings)

    # Force string type
    env = {str(k): str(v) for k, v in env.items()}

    if verbose:  # pragma: no cover
        print_env(env, separator)

    return env
