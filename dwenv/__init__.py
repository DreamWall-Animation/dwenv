try:
    # python 2
    from env import build_env
except ModuleNotFoundError:
    # python 3
    from dwenv.env import build_env
