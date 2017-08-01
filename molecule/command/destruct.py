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

import click

import molecule.command
from molecule import logger
from molecule import scenarios
from molecule.command import base

LOG = logger.get_logger(__name__)


class Destruct(base.Base):
    """
    This is a destructive action and not enabled by default.   See the
    provisioners documentation for further details.

    Target the default scenario:

    >>> molecule destruct

    Targeting a specific scenario:

    >>> molecule destruct --scenario-name foo

    Executing with `debug`:

    >>> molecule --debug destruct
    """

    def execute(self):
        """
        Execute the actions necessary to perform a `molecule destruct` and
        returns None.

        :return: None
        """
<<<<<<< HEAD
        if not self._config.provisioner.playbooks.destruct:
            msg = 'Skipping, destruct playbook not configured.'
            LOG.warn(msg)
            return

=======
>>>>>>> Implement an internal test matrix
        self._config.provisioner.destruct()


@click.command()
@click.pass_context
@click.option(
    '--scenario-name',
    '-s',
    default='default',
    help='Name of the scenario to target. (default)')
def destruct(ctx, scenario_name):  # pragma: no cover
    """ Use a provisioner to destruct instances. """
    args = ctx.obj.get('args')
    command_args = {
        'subcommand': __name__,
    }

    s = scenarios.Scenarios(
        base.get_configs(args, command_args), scenario_name)
    s.print_matrix()
    for scenario in s.all:
        for sequence in s.sequences_for_scenario(scenario):
            s.print_sequence_info(scenario, sequence)
            command_module = getattr(molecule.command, sequence)
            command = getattr(command_module, sequence.capitalize())
            command(scenario.config).execute()
