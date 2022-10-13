# dwenv
Launch applications with environment variables from multiple config files.

![.env & .envc hierarchy][image]

[image]: hierarchy.png "files hierarchy"

## Example:
python dwenv/launcher.py --config `maya_np.env` --executable maya

* `maya_np.env` content:
    ```
    np_configs_dir/prod.envc
    np_configs_dir/maya.envc
    np_configs_dir/animschoolpicker.envc
    ...
    ```

* `prod.envc` content:
    ```
    PROD_NAME = Neti Pikola
    PROD_CODE = NP
    FRAMERATE = 25
    PROD_ROOT = /path/to/prod_root
    SOFTWARE_ROOT = ${PROD_ROOT}/software
    PYTHONPATH > ${SOFTWARE_ROOT}/prodlib
    ...
    ```

* `maya.envc` content:
    ```
    PATH > ${MAYA_LOCATION}/bin
    MAYA_VP2_DEVICE_OVERRIDE = VirtualDeviceGL
    ...
    ```

* `animschoolpicker.envc` content:
    ```
    MAYA_PLUG_IN_PATH.windows > ${SOFTWARE_ROOT}/animschoolpicker/windows/2018
    MAYA_PLUG_IN_PATH.linux > ${SOFTWARE_ROOT}/animschoolpicker/linux/2018
    ...
    ```

## Commandline arguments:
    --config (-c)       Environment config path
    --executable (-x)   Executable path
    --arguments (-a)    Executable arguments. Use quotes: -a="..."
    --dry-run (-d)      Prints resulting environment without running anything


## Configs syntax:
Each .envc line look like this:\
`ENV_NAME(.platform) [operator] value`
- There is three operators for .envc files. Spaces around them are **mandatory**:
    * " `=` " will set or replace a variable. Replacing an existing variable will print a warning.
    * " `>` " appends string/path to existing variable with os path separator (`:`/`;`)
    * " `<` " prepends ...

- If a variable must be set for a specific operating system, add `[.platform]` to variable name:
    * "`VAR.windows = x`"
    * "`VAR.linux = y`"
    * "`VAR.darwin = z`"
    * ...

- All environment expressions will be expanded if they exists. Thus, the order of the environment configs matter.\
There is no other dependency trickery. Just list what you need.

- You can comment a line with "`#`".


## As a python module:
```python
import dwenv.env
env = dwenv.env.build_env(
        configs_paths=None, from_current_env=True, start_env=None,
        vars_to_remove=None, override_warnings=False, target_platform=None)
```
Using `launcher.py` or `build_env` function will also set DWENV_CONFIG var to know which config was used to generate the environment. You can then later re-use this path together with the `target_platform` argument if you need to send a job on another platform.
