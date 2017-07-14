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

import operator

import tree_format

from molecule import logger
from molecule import util

LOG = logger.get_logger(__name__)


class Scenarios(object):
    """
    The Scenarios object consists of one to many scenario objects Molecule will
    execute.
    """

    def __init__(self, configs, scenario_name=None):
        """
        Initialize a new scenarios class and returns None.

        :param configs: A list containing Molecule config instances.
        :return: None
        """
        self._configs = configs
        self._scenario_name = scenario_name
        self._logged = False
        self._matrix = self._get_matrix()

    @property
    def all(self):
        """
        All scenario objects filtered and veriried and returns a list.

        :return: list
        """
        if self._scenario_name:
            scenarios = self._filter_for_scenario(self._scenario_name)
            self._verify()

            return scenarios

        return [c.scenario for c in self._configs]

    def print_matrix(self):
        msg = 'Test matrix'
        LOG.info(msg)

        tree = tuple(('', [(scenario.name,
                            [(sequence, [])
                             for sequence in self.sequences_for_scenario(
                                 scenario, skipped=True)])
                           for scenario in self.all]))

        tf = tree_format.format_tree(
            tree,
            format_node=operator.itemgetter(0),
            get_children=operator.itemgetter(1))

        LOG.out(tf.encode('utf-8'))

    def print_sequence_info(self, scenario, sequence):
        msg = "Scenario: '{}'".format(scenario.name)
        LOG.info(msg)
        msg = "Sequence: '{}'".format(sequence)
        LOG.info(msg)

    def sequences_for_scenario(self, scenario, skipped=False):
        """
        Select the sequence based on scenario and subcommand of the provided
        scenario object and returns a list.

        :param scenario: A scenario object.
        :param skipped: An optional bool to include skipped scenarios.
        :return: list
        """
        matrix = self._get_matrix()

        try:
            if skipped:
                return matrix[scenario.name][scenario.subcommand]
            else:
                return [
                    sequence
                    for sequence in matrix[scenario.name][scenario.subcommand]
                    if 'skipping' not in sequence
                ]
        except KeyError:
            # TODO(retr0h): May change this handling in the future.
            return []

    def _verify(self):
        """
        Verify the specified scenario was found and returns None.

        :return: None
        """
        scenario_names = [c.scenario.name for c in self._configs]
        if self._scenario_name not in scenario_names:
            msg = ("Scenario '{}' not found.  "
                   'Exiting.').format(self._scenario_name)
            util.sysexit_with_message(msg)

    def _filter_for_scenario(self, scenario_name):
        """
        Find the config matching the provided scenario name and returns a list.

        :param scenario_name: A string containing the name of the scenario's
         object to find and return.
        :return: list
        """

        return [
            c.scenario for c in self._configs
            if c.scenario.name == scenario_name
        ]

    def _filter_sequences(self, scenario, sequences):
        """
        Remove sequences which should not be executed and returns a list.

        :param sequences: A list containing the scenario's subcommand
         sequences.
        :param scenario: A scenario object.
        :return: list
        """
        if scenario.config.driver.name == 'delegated':
            msg = logger.yellow_text('skipping - instances are delegated')

            sequences = [
                sequence if (sequence not in [
                    scenario.setup_sequence, scenario.teardown_sequence
                ]) else '{} ({})'.format(sequence, msg)
                for sequence in sequences
            ]

        if scenario.config.state.created:
            msg = logger.yellow_text('skipping - instances already created')

            sequences = [
                sequence if (sequence not in [scenario.setup_sequence]) else
                '{} ({})'.format(sequence, msg) for sequence in sequences
            ]

        if not scenario.config.provisioner.playbooks.destruct:
            msg = logger.yellow_text(
                'skipping - destruct playbook not configured')

            sequences = [
                sequence if (sequence not in [scenario.destruct_sequence]) else
                '{} ({})'.format(sequence, msg) for sequence in sequences
            ]

        if not scenario.config.dependency.enabled:
            msg = logger.yellow_text('skipping - dependency is disabled')

            sequences = [
                sequence if (sequence not in [scenario.dependency_sequence])
                else '{} ({})'.format(sequence, msg) for sequence in sequences
            ]

        if not scenario.config.lint.enabled:
            msg = logger.yellow_text('skipping - lint is disabled')

            sequences = [
                sequence if (sequence not in ['scenario.lint_sequence']) else
                '{} ({})'.format(sequence, msg) for sequence in sequences
            ]

        if not scenario.config.state.converged:
            msg = logger.yellow_text('skipping - instances not converged')

            sequences = [
                sequence if (sequence not in ['scenario.idempotence_sequence'])
                else '{} ({})'.format(sequence, msg) for sequence in sequences
            ]

        return sequences

    def _get_matrix(self):
        """
        Build a matrix of scenarios with sequences to execute and returns a
        dict.

        {
            scenario_1: {
                'subcommand': [
                    'sequence-1',
                    'sequence-2',
                ],
            },
            scenario_2: {
                'subcommand': [
                    'sequence-1',
                ],
            },
        }

        :returns: dict
        """
        return dict({
            scenario.name: {
                'check':
                self._filter_sequences(scenario, scenario.check_sequences),
                'converge':
                self._filter_sequences(scenario, scenario.converge_sequences),
                'create':
                self._filter_sequences(scenario, scenario.create_sequences),
                'dependency':
                self._filter_sequences(scenario,
                                       scenario.dependency_sequences),
                'destroy':
                self._filter_sequences(scenario, scenario.destroy_sequences),
                'destruct':
                self._filter_sequences(scenario, scenario.destruct_sequences),
                'idempotence':
                self._filter_sequences(scenario,
                                       scenario.idempotence_sequences),
                'lint':
                self._filter_sequences(scenario, scenario.lint_sequences),
                'syntax':
                self._filter_sequences(scenario, scenario.syntax_sequences),
                'test':
                self._filter_sequences(scenario, scenario.test_sequences),
                'verify':
                self._filter_sequences(scenario, scenario.verify_sequences),
            }
            for scenario in self.all
        })
