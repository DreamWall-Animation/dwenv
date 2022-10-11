__copyright__ = 'DreamWall'
__author__ = 'Olivier Evers'
__license__ = 'MIT'


import os
import re
import sys
from platform import system


PLATFORM = system().lower()


def expand_variables(path, env):
    for k, v in env.items():
        path = path.replace('${%s}' % k, v)
    return path


def is_string(var):
    """For Python2/3 compatiblity"""
    if sys.version_info >= (3, 0):
        return isinstance(var, str)
    else:
        return isinstance(var, basestring)


def get_separator(platform=PLATFORM):
    if platform == 'windows':
        return ';'
    else:
        return ':'


def get_start_env(from_current_env=True, start_env=None, keys_to_remove=None):
    if not from_current_env:
        return start_env or {}

    env = os.environ.copy()
    if keys_to_remove:
        for k in keys_to_remove:
            env.pop(k, None)
    return env


def conform_configs_paths_var(configs_paths):
    """
    returns list of .envc files.
    if configs_paths is a single .env file, it will return its content.
    if it's is a single .envc file, it will return it as a single item list.
    """
    if not is_string(configs_paths):
        return configs_paths
    elif configs_paths.endswith('.envc'):
        return [configs_paths]
    elif configs_paths.endswith('.env'):
        if not os.path.exists(configs_paths):
            raise ValueError('Config file missing: %s' % configs_paths)
        with open(configs_paths, 'r') as f:
            return [l.strip() for l in f.readlines() if l]
    else:
        raise ValueError('Wrong value passed for configs_paths')


def print_env(env, separator=None):
    separator = separator or get_separator()
    for var in sorted(env.keys()):
        print('\n' + var)
        for path in env[var].split(separator):
            print(' - ' + path)


def extend_env_with_envconfig(
        env, target_platform, config_path, override_warnings=True):
    if not os.path.exists(config_path):
        raise ValueError('Config file missing: %s' % config_path)
    if not config_path.endswith('.envc'):
        raise ValueError('Wrong file extension: %s' % config_path)

    separator = get_separator(target_platform)

    with open(config_path, 'r') as config:
        for line in config:
            line = line.strip()
            if not line:
                continue
            if line.startswith(('#', '//')):
                continue

            # Parse for variable, operator, (platform) and value
            try:
                variable, operator, value = re.split(
                    r'(\s=\s|\s>\s|\s<\s)', line)
            except ValueError:
                print('Wrong input: %s' % line)
                raise
            try:
                variable, platform = re.split(r'\.', variable)
            except ValueError:
                platform = None

            # Skip values for other platforms:
            if platform is not None and platform != target_platform:
                continue

            # Check operator value
            if operator not in (' = ', ' > ', ' < '):
                raise ValueError('Unknown operator "%s"' % operator)

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
        configs_paths=None, from_current_env=True, start_env=None,
        keys_to_remove=None, override_warnings=True, target_platform=None,
        verbose=False):
    """
    configs_path: you can pass a single .env config path or a list of .envc's
    """
    target_platform = target_platform or PLATFORM
    separator = get_separator(target_platform)
    env = get_start_env(from_current_env, start_env, keys_to_remove)

    if configs_paths is None:
        # Use DWENV_CONFIG value if no configs_paths provided:
        configs_paths = os.environ['DWENV_CONFIG']
    else:
        env['DWENV_CONFIG'] = configs_paths
    configs_paths = conform_configs_paths_var(configs_paths)

    # Build from configs:
    for config_path in configs_paths:
        if not config_path:
            continue
        if config_path.startswith('#'):
            continue
        config_path = os.path.expandvars(config_path)
        extend_env_with_envconfig(
            env, target_platform, config_path, override_warnings)

    # Update PATH to make sure executable is found
    for path in env.get('PATH', '').split(separator):
        if path not in os.environ['PATH']:
            os.environ['PATH'] += separator + path

    # Force string type
    env = {str(k): str(v) for k, v in env.items()}

    if verbose:
        print_env(env, separator)

    return env
