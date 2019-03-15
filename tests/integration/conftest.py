from os import getenv
import pytest


def skipif_not_all_env_vars_set(env_vars_list):
    requirements_met = all(getenv(item) for item in env_vars_list)
    return pytest.mark.skipif(
        not requirements_met, reason=f"you have to have set env vars: {env_vars_list}"
    )
