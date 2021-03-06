#  Copyright (c) 2015-2017 Cisco Systems, Inc.
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to
#  deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.

import os
import shutil

import pytest

from molecule import config
from molecule import util
from molecule.command import base


class ExtendedBase(base.Base):
    def execute():
        pass


@pytest.fixture
def base_class(config_instance):
    return ExtendedBase


@pytest.fixture
def base_instance(base_class, config_instance):
    return base_class(config_instance)


def test_config_private_member(base_instance):
    assert isinstance(base_instance._config, config.Config)


def test_init_calls_setup(patched_base_setup, base_instance):
    patched_base_setup.assert_called_once_with()


def test_prune(base_instance):
    ephemeral_directory = base_instance._config.ephemeral_directory

    foo_file = os.path.join(ephemeral_directory, 'foo')
    bar_file = os.path.join(ephemeral_directory, 'bar')
    baz_directory = os.path.join(ephemeral_directory, 'baz')
    state_file = os.path.join(ephemeral_directory, 'state.yml')
    inventory_file = os.path.join(ephemeral_directory, 'ansible_inventory.yml')
    config_file = os.path.join(ephemeral_directory, 'ansible.cfg')

    os.mkdir(baz_directory)
    for f in [foo_file, bar_file, state_file]:
        open(f, 'a').close()

    base_instance.prune()

    assert not os.path.isfile(foo_file)
    assert not os.path.isfile(bar_file)
    assert os.path.isfile(state_file)
    assert os.path.isfile(config_file)
    assert os.path.isfile(inventory_file)
    assert os.path.isdir(baz_directory)


def test_setup(mocker, patched_provisioner_add_or_update_vars,
               patched_provisioner_write_inventory,
               patched_provisioner_write_config, base_instance):

    assert os.path.isdir(base_instance._config.ephemeral_directory)
    assert os.path.isdir(
        os.path.dirname(base_instance._config.provisioner.inventory_file))

    patched_provisioner_write_inventory.assert_called_once_with()
    patched_provisioner_write_config.assert_called_once_with()

    x = [mocker.call('host_vars'), mocker.call('group_vars')]
    assert x == patched_provisioner_add_or_update_vars.mock_calls


def test_setup_creates_ephemeral_directory(base_instance):
    ephemeral_directory = base_instance._config.ephemeral_directory
    shutil.rmtree(base_instance._config.ephemeral_directory)
    base_instance._setup()

    assert os.path.isdir(ephemeral_directory)


def test_verify_configs(config_instance):
    configs = [config_instance]

    assert base._verify_configs(configs) is None


def test_verify_configs_raises_with_no_configs(patched_logger_critical):
    with pytest.raises(SystemExit) as e:
        base._verify_configs([])

    assert 1 == e.value.code

    msg = "'molecule/*/molecule.yml' glob failed.  Exiting."
    patched_logger_critical.assert_called_once_with(msg)


def test_verify_configs_raises_with_duplicate_configs(patched_logger_critical,
                                                      config_instance):
    with pytest.raises(SystemExit) as e:
        configs = [config_instance, config_instance]
        base._verify_configs(configs)

    assert 1 == e.value.code

    msg = "Duplicate scenario name 'default' found.  Exiting."
    patched_logger_critical.assert_called_once_with(msg)


def test_verify_scenario_name(config_instance):
    configs = [config_instance]

    assert base._verify_scenario_name(configs, 'default') is None


def test_verify_scenario_name_raises_when_scenario_not_found(
        config_instance, patched_logger_critical):
    configs = [config_instance]
    with pytest.raises(SystemExit) as e:
        base._verify_scenario_name(configs, 'foo')

    assert 1 == e.value.code

    msg = "Scenario 'foo' not found.  Exiting."
    patched_logger_critical.assert_called_once_with(msg)


def test_get_configs(config_instance):
    molecule_file = config_instance.molecule_file
    data = config_instance.config
    util.write_file(molecule_file, util.safe_dump(data))

    result = base.get_configs({}, {})
    assert 1 == len(result)
    assert isinstance(result, list)
    assert isinstance(result[0], config.Config)


def test_get_configs_calls_verify_scenario_name(
        mocker, config_instance, patched_verify_configs,
        patched_base_filter_configs_for_scenario,
        patched_verify_scenario_name):
    patched_base_filter_configs_for_scenario.return_value = [config_instance]
    base.get_configs({}, {'scenario_name': 'default'})

    patched_verify_scenario_name.assert_called_once_with(
        patched_base_filter_configs_for_scenario.return_value, 'default')


def test_get_configs_calls_verify_configs(patched_verify_configs):
    base.get_configs({}, {})

    patched_verify_configs.assert_called_once_with([])


def test_get_configs_filter_configs_for_scenario(
        mocker,
        patched_verify_configs,
        patched_base_filter_configs_for_scenario,
        patched_verify_scenario_name, ):
    base.get_configs({}, {'scenario_name': 'default'})

    patched_base_filter_configs_for_scenario.assert_called_once_with('default',
                                                                     [])


def test_filter_configs_for_scenario(config_instance):
    configs = [config_instance, config_instance]

    result = base._filter_configs_for_scenario('default', configs)
    assert 2 == len(result)

    result = base._filter_configs_for_scenario('invalid', configs)
    assert [] == result
