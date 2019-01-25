# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import threading

import plumpy
from plumpy.utils import AttributesFrozendict

from aiida import work
from aiida.backends.testbase import AiidaTestCase
from aiida.common.lang import override
from aiida.orm import load_node
from aiida.orm.nodes.data.int import Int
from aiida.orm.nodes.data.str import Str
from aiida.orm.nodes.data.frozendict import FrozenDict
from aiida.orm.nodes.data.parameter import ParameterData
from aiida.orm.node import WorkflowNode
from aiida.work import test_utils, Process


class NameSpacedProcess(work.Process):

    _node_class = WorkflowNode

    @classmethod
    def define(cls, spec):
        super(NameSpacedProcess, cls).define(spec)
        spec.input('some.name.space.a', valid_type=Int)


class TestProcessNamespace(AiidaTestCase):

    def setUp(self):
        super(TestProcessNamespace, self).setUp()
        self.assertIsNone(Process.current())

    def tearDown(self):
        super(TestProcessNamespace, self).tearDown()
        self.assertIsNone(Process.current())

    def test_namespaced_process(self):
        """
        Test that inputs in nested namespaces are properly validated and the link labels
        are properly formatted by connecting the namespaces with underscores
        """
        proc = NameSpacedProcess(inputs={'some': {'name': {'space': {'a': Int(5)}}}})

        # Test that the namespaced inputs are AttributesFrozenDicts
        self.assertIsInstance(proc.inputs, AttributesFrozendict)
        self.assertIsInstance(proc.inputs.some, AttributesFrozendict)
        self.assertIsInstance(proc.inputs.some.name, AttributesFrozendict)
        self.assertIsInstance(proc.inputs.some.name.space, AttributesFrozendict)

        # Test that the input node is in the inputs of the process
        input_node = proc.inputs.some.name.space.a
        self.assertTrue(isinstance(input_node, Int))
        self.assertEquals(input_node.value, 5)

        # Check that the link of the process node has the correct link name
        self.assertTrue('some_name_space_a' in proc.node.get_incoming().all_link_labels())
        self.assertEquals(proc.node.get_incoming().get_node_by_label('some_name_space_a'), 5)


class ProcessStackTest(work.Process):

    _node_class = WorkflowNode

    @override
    def run(self):
        pass

    @override
    def on_create(self):
        super(ProcessStackTest, self).on_create()
        self._thread_id = threading.current_thread().ident

    @override
    def on_stop(self):
        # The therad must match the one used in on_create because process
        # stack is using thread local storage to keep track of who called who
        super(ProcessStackTest, self).on_stop()
        assert self._thread_id is threading.current_thread().ident


class TestProcess(AiidaTestCase):

    def setUp(self):
        super(TestProcess, self).setUp()
        self.assertIsNone(Process.current())

    def tearDown(self):
        super(TestProcess, self).tearDown()
        self.assertIsNone(Process.current())

    def test_process_stack(self):
        work.launch.run(ProcessStackTest)

    def test_inputs(self):
        with self.assertRaises(TypeError):
            work.launch.run(work.test_utils.BadOutput)

    def test_input_link_creation(self):
        dummy_inputs = ["1", "2", "3", "4"]

        inputs = {l: Int(l) for l in dummy_inputs}
        inputs['metadata'] = {'store_provenance': True}
        process = test_utils.DummyProcess(inputs)

        for entry in process.node.get_incoming().all():
            self.assertTrue(entry.link_label in inputs)
            self.assertEqual(int(entry.link_label), int(entry.node.value))
            dummy_inputs.remove(entry.link_label)

        # Make sure there are no other inputs
        self.assertFalse(dummy_inputs)

    def test_none_input(self):
        # Check that if we pass no input the process runs fine
        work.launch.run(test_utils.DummyProcess)

    def test_seal(self):
        pid = work.launch.run_get_pid(test_utils.DummyProcess).pid
        self.assertTrue(load_node(pk=pid).is_sealed)

    def test_description(self):
        dp = test_utils.DummyProcess(inputs={'metadata': {'description': "Rockin' process"}})
        self.assertEquals(dp.node.description, "Rockin' process")

        with self.assertRaises(ValueError):
            test_utils.DummyProcess(inputs={'metadata': {'description': 5}})

    def test_label(self):
        dp = test_utils.DummyProcess(inputs={'metadata': {'label': 'My label'}})
        self.assertEquals(dp.node.label, 'My label')

        with self.assertRaises(ValueError):
            test_utils.DummyProcess(inputs={'label': 5})

    def test_work_calc_finish(self):
        p = test_utils.DummyProcess()
        self.assertFalse(p.node.is_finished_ok)
        work.launch.run(p)
        self.assertTrue(p.node.is_finished_ok)

    def test_calculation_input(self):
        @work.calcfunction
        def simple_wf():
            return {'a': Int(6), 'b': Int(7)}

        outputs, pid = work.launch.run_get_pid(simple_wf)
        calc = load_node(pid)

        dp = test_utils.DummyProcess(inputs={'calc': calc})
        work.launch.run(dp)

        input_calc = dp.node.get_incoming().get_node_by_label('calc')
        self.assertTrue(isinstance(input_calc, FrozenDict))
        self.assertEqual(input_calc['a'], outputs['a'])

    def test_save_instance_state(self):
        proc = test_utils.DummyProcess()
        # Save the instance state
        bundle = plumpy.Bundle(proc)
        proc.close()
        bundle.unbundle()

    def test_process_type_with_entry_point(self):
        """
        For a process with a registered entry point, the process_type will be its formatted entry point string
        """
        from aiida.orm import CalculationFactory, Code

        code = Code()
        code.set_remote_computer_exec((self.computer, '/bin/true'))
        code.store()

        parameters = ParameterData(dict={})
        template = ParameterData(dict={})
        options = {
            'resources': {
                'num_machines': 1,
                'tot_num_mpiprocs': 1
            },
            'max_wallclock_seconds': 1,
        }

        inputs = {
            'code': code,
            'parameters': parameters,
            'template': template,
            'metadata': {
                'options': options,
            }
        }

        entry_point = 'templatereplacer'
        process_class = CalculationFactory(entry_point)
        process = process_class(inputs=inputs)

        expected_process_type = 'aiida.calculations:{}'.format(entry_point)
        self.assertEqual(process.node.process_type, expected_process_type)

        # Verify that load_process_class on the calculation node returns the original entry point class
        recovered_process = process.node.load_process_class()
        self.assertEqual(recovered_process, process_class)

    def test_process_type_without_entry_point(self):
        """
        For a process without a registered entry point, the process_type will fall back on the fully
        qualified class name
        """
        process = test_utils.DummyProcess()
        expected_process_type = '{}.{}'.format(process.__class__.__module__, process.__class__.__name__)
        self.assertEqual(process.node.process_type, expected_process_type)

        # Verify that load_process_class on the calculation node returns the original entry point class
        recovered_process = process.node.load_process_class()
        self.assertEqual(recovered_process, process.__class__)

    def test_validation_error(self):
        """Test that validating a port produces an meaningful message"""

        class TestProc(work.Process):
            @classmethod
            def define(cls, spec):
                super(TestProc, cls).define(spec)
                spec.input('a.b', valid_type=Str)

        with self.assertRaises(ValueError) as context:
            TestProc({'a': {'b': Int(5)}})
        self.assertIn('inputs.a.b', str(context.exception))
