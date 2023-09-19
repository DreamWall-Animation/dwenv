__copyright__ = 'DreamWall'
__author__ = 'Olivier Evers'
__license__ = 'MIT'


import os
import sys
import shlex
import subprocess
import pprint

from env import build_env, PLATFORM


sys.dont_write_bytecode = True


def launch(
        executable, arguments=None, env_configs=None, start_env='current',
        vars_to_remove=None, dry=False):
    # Build command line:
    if isinstance(arguments, str):
        arguments = shlex.split(arguments)
    elif arguments is None:
        arguments = []
    command = [executable] + arguments

    # Build env:
    env = build_env(
        env_configs, start_env=start_env,
        vars_to_remove=vars_to_remove, override_warnings=True, verbose=dry)

    # Launch:
    if dry:
        return
    try:
        if PLATFORM == 'linux':
            subprocess.call(command, env=env)
        else:
            if any(s in executable for s in ('cmd', 'powershell', 'pwsh')):
                subprocess.call(command, env=env, shell=True)
            else:
                subprocess.Popen(command, env=env)
    except TypeError:
        pprint.pprint(env)
        raise
    except FileNotFoundError:
        print(f'\n\n\nFailed to launch following command: {command}\n')
        print('Env "PATH" =')
        print()
        print(env['PATH'])
        print()
        pprint.pprint(env['PATH'].split(os.pathsep))
        print('\n\n')
        raise


if __name__ == '__main__':
    import argparse
    description = (
        'Launch applications with environment variables from multiple config '
        'files.\nhttps://github.com/DreamWall-Animation/dwenv')
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '-c', '--config', help='Environment config path', required=True)
    parser.add_argument(
        '-x', '--executable', help='Executable path', required=True)
    parser.add_argument(
        '-a', '--arguments', help='Executable arguments (usage: -a="...")')
    parser.add_argument(
        '-d', '--dry-run', help='Prints environment without launching app',
        action='store_true')
    args = parser.parse_args()
    launch(
        args.executable,
        arguments=args.arguments,
        env_configs=args.config,
        dry=args.dry_run)
