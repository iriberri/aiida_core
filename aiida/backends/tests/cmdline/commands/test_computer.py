"""Tests for the 'verdi computer' command."""
import os
from collections import OrderedDict
from click.testing import CliRunner
from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands.cmd_computer import disable_computer, enable_computer, setup_computer
from aiida.cmdline.commands.cmd_computer import computer_show, computer_list, computer_rename, computer_delete
from aiida.cmdline.commands.cmd_computer import computer_test, computer_configure


def generate_setup_options_dict(replace_args={}, non_interactive=True):
    """
    Return a OrderedDict with the key-value pairs for the command line.

    I use an ordered dict because for changing entries it's easier
    to have keys (so, a dict) but the commands might require a specific order,
    so I use an OrderedDict.

    This should be then passed to ``generate_setup_options()``.

    :param replace_args: a dictionary with the keys to replace, if needed
    :return: an OrderedDict with the command-line options
    """
    valid_noninteractive_options = OrderedDict()

    if non_interactive:
        valid_noninteractive_options['non-interactive'] = None
    valid_noninteractive_options['label'] = 'noninteractive_computer'
    valid_noninteractive_options['hostname'] = "localhost"
    valid_noninteractive_options['description'] = "my description"
    # Specifically give a string value for interactive prompts
    if not non_interactive:
        valid_noninteractive_options['enabled'] = "True"
    valid_noninteractive_options['transport'] = "local"
    valid_noninteractive_options['scheduler'] = "direct"
    valid_noninteractive_options['shebang'] = "#!/bin/bash"
    valid_noninteractive_options['work-dir'] = "/scratch/{username}/aiida_run"
    valid_noninteractive_options['mpirun-command'] = "mpirun -np {tot_num_mpiprocs}"
    valid_noninteractive_options['mpiprocs-per-machine'] = "2"
    # Make them multiline to test also multiline options
    valid_noninteractive_options['prepend-text'] = "date\necho 'second line'"
    valid_noninteractive_options['append-text'] = "env\necho '444'\necho 'third line'"

    # I replace kwargs here, so that if they are known, they go at the right order
    for k in replace_args:
        valid_noninteractive_options[k] = replace_args[k]

    return valid_noninteractive_options


def generate_setup_options(ordereddict):
    """
    Given an (ordered) dict, returns a list of options

    Note that at this moment the implementation only supports long options
    (i.e. --option=value) and not short ones (-o value).
    Set a value to None to avoid the '=value' part.

    :param ordereddict: as generated by ``generate_setup_options_dict()``
    :return: a list to be passed as command-line arguments.
    """
    options = []
    for key, value in ordereddict.iteritems():
        if value is None:
            options.append('--{}'.format(key))
        else:
            options.append('--{}={}'.format(key, value))
    return options


def generate_setup_options_interactive(ordereddict):
    """
    Given an (ordered) dict, returns a list of options

    Note that at this moment the implementation only supports long options
    (i.e. --option=value) and not short ones (-o value).
    Set a value to None to avoid the '=value' part.

    :param ordereddict: as generated by ``generate_setup_options_dict()``
    :return: a list to be passed as command-line arguments.
    """
    options = []
    for key, value in ordereddict.iteritems():
        if value is None:
            options.append(True)
        else:
            options.append(value)
    return options


class TestVerdiComputerSetup(AiidaTestCase):
    """Tests for the 'verdi computer setup' command."""

    def setUp(self):
        self.runner = CliRunner()

    def test_help(self):
        self.runner.invoke(setup_computer, ['--help'], catch_exceptions=False)

    def test_reachable(self):
        import subprocess as sp
        output = sp.check_output(['verdi', 'computer', 'setup', '--help'])
        self.assertIn('Usage:', output)

    def test_interactive(self):
        from aiida.orm import Computer
        os.environ['VISUAL'] = 'sleep 1; vim -cwq'
        os.environ['EDITOR'] = 'sleep 1; vim -cwq'
        label = 'interactive_computer'

        options_dict = generate_setup_options_dict(replace_args={'label': label}, non_interactive=False)
        # In any case, these would be managed by the visual editor
        options_dict.pop('prepend-text')
        options_dict.pop('append-text')
        user_input = "\n".join(generate_setup_options_interactive(options_dict))

        result = self.runner.invoke(setup_computer, input=user_input)
        self.assertIsNone(result.exception, msg="There was an unexpected exception. Output: {}".format(result.output))

        new_computer = Computer.get(label)
        self.assertIsInstance(new_computer, Computer)

        self.assertEqual(new_computer.description, options_dict['description'])
        self.assertEqual(new_computer.hostname, options_dict['hostname'])
        self.assertEqual(new_computer.get_transport_type(), options_dict['transport'])
        self.assertEqual(new_computer.get_scheduler_type(), options_dict['scheduler'])
        self.assertTrue(new_computer.is_enabled())
        self.assertEqual(new_computer.get_mpirun_command(), options_dict['mpirun-command'].split())
        self.assertEqual(new_computer.get_shebang(), options_dict['shebang'])
        self.assertEqual(new_computer.get_workdir(), options_dict['work-dir'])
        self.assertEqual(new_computer.get_default_mpiprocs_per_machine(), int(options_dict['mpiprocs-per-machine']))
        # For now I'm not writing anything in them
        self.assertEqual(new_computer.get_prepend_text(), "")
        self.assertEqual(new_computer.get_append_text(), "")

    def test_mixed(self):
        from aiida.orm import Computer
        os.environ['VISUAL'] = 'sleep 1; vim -cwq'
        os.environ['EDITOR'] = 'sleep 1; vim -cwq'
        label = 'mixed_computer'

        options_dict = generate_setup_options_dict(replace_args={'label': label})
        options_dict_full = options_dict.copy()

        options_dict.pop('non-interactive', 'None')

        non_interactive_options_dict = {}
        non_interactive_options_dict['enabled'] = None

        non_interactive_options_dict['prepend-text'] = options_dict.pop('prepend-text')
        non_interactive_options_dict['append-text'] = options_dict.pop('append-text')
        non_interactive_options_dict['shebang'] = options_dict.pop('shebang')
        non_interactive_options_dict['scheduler'] = options_dict.pop('scheduler')

        # In any case, these would be managed by the visual editor
        user_input = "\n".join(generate_setup_options_interactive(options_dict))
        options = generate_setup_options(non_interactive_options_dict)

        result = self.runner.invoke(setup_computer, options, input=user_input)
        self.assertIsNone(result.exception, msg="There was an unexpected exception. Output: {}".format(result.output))

        new_computer = Computer.get(label)
        self.assertIsInstance(new_computer, Computer)

        self.assertEqual(new_computer.description, options_dict_full['description'])
        self.assertEqual(new_computer.hostname, options_dict_full['hostname'])
        self.assertEqual(new_computer.get_transport_type(), options_dict_full['transport'])
        self.assertEqual(new_computer.get_scheduler_type(), options_dict_full['scheduler'])
        self.assertTrue(new_computer.is_enabled())
        self.assertEqual(new_computer.get_mpirun_command(), options_dict_full['mpirun-command'].split())
        self.assertEqual(new_computer.get_shebang(), options_dict_full['shebang'])
        self.assertEqual(new_computer.get_workdir(), options_dict_full['work-dir'])
        self.assertEqual(new_computer.get_default_mpiprocs_per_machine(),
                         int(options_dict_full['mpiprocs-per-machine']))
        # For now I'm not writing anything in them
        self.assertEqual(new_computer.get_prepend_text(), options_dict_full['prepend-text'])
        self.assertEqual(new_computer.get_append_text(), options_dict_full['append-text'])

    def test_noninteractive(self):
        """
        Main test to check if the non-interactive command works
        """
        from aiida.orm import Computer

        options_dict = generate_setup_options_dict()
        options = generate_setup_options(options_dict)

        result = self.runner.invoke(setup_computer, options)

        self.assertIsNone(result.exception, result.output[-1000:])
        new_computer = Computer.get(options_dict['label'])
        self.assertIsInstance(new_computer, Computer)

        self.assertEqual(new_computer.description, options_dict['description'])
        self.assertEqual(new_computer.hostname, options_dict['hostname'])
        self.assertEqual(new_computer.get_transport_type(), options_dict['transport'])
        self.assertEqual(new_computer.get_scheduler_type(), options_dict['scheduler'])
        self.assertTrue(new_computer.is_enabled())
        self.assertEqual(new_computer.get_mpirun_command(), options_dict['mpirun-command'].split())
        self.assertEqual(new_computer.get_shebang(), options_dict['shebang'])
        self.assertEqual(new_computer.get_workdir(), options_dict['work-dir'])
        self.assertEqual(new_computer.get_default_mpiprocs_per_machine(), int(options_dict['mpiprocs-per-machine']))
        self.assertEqual(new_computer.get_prepend_text(), options_dict['prepend-text'])
        self.assertEqual(new_computer.get_append_text(), options_dict['append-text'])

        # Test that I cannot generate twice a computer with the same label
        result = self.runner.invoke(setup_computer, options)
        self.assertIsInstance(result.exception, SystemExit)
        self.assertIn("already exists", result.output)

    def test_noninteractive_disabled(self):
        """
        I check what happens if the computer should be disabled.

        I only check the changes, the rest is already checked in ``test_noninteractive()``.
        """
        from aiida.orm import Computer

        options_dict = generate_setup_options_dict({
            'label': 'computer_disabled',
            ## Pass the '--disabled' option
            'disabled': None
        })
        options_dict.pop('enabled', None)  # Make sure --enabled is not there
        options = generate_setup_options(options_dict)

        result = self.runner.invoke(setup_computer, options)

        self.assertIsNone(result.exception, result.output[-1000:])
        new_computer = Computer.get(options_dict['label'])
        self.assertIsInstance(new_computer, Computer)
        self.assertFalse(new_computer.is_enabled())

    def test_noninteractive_enabled(self):
        """
        I check what happens if the computer should be enabled, explicitly setting
        --enabled.

        I only check the changes, the rest is already checked in ``test_noninteractive()``.
        """
        from aiida.orm import Computer

        options_dict = generate_setup_options_dict({'label': 'computer_enabled'})
        options_dict.pop('disabled', None)  # Make sure 'disabled' is not there
        options_dict['enabled'] = None  # Activate --enabled
        options = generate_setup_options(options_dict)

        result = self.runner.invoke(setup_computer, options)

        self.assertIsNone(result.exception, result.output[-1000:])
        new_computer = Computer.get(options_dict['label'])
        self.assertIsInstance(new_computer, Computer)
        self.assertTrue(new_computer.is_enabled())

    def test_noninteractive_optional_default_mpiprocs(self):
        """
        Check that if is ok not to specify mpiprocs-per-machine
        """
        from aiida.orm import Computer

        options_dict = generate_setup_options_dict({'label': 'computer_default_mpiprocs'})
        options_dict.pop('mpiprocs-per-machine')
        options = generate_setup_options(options_dict)
        result = self.runner.invoke(setup_computer, options)

        self.assertIsNone(result.exception, result.output[-1000:])

        new_computer = Computer.get(options_dict['label'])
        self.assertIsInstance(new_computer, Computer)
        self.assertIsNone(new_computer.get_default_mpiprocs_per_machine())

    def test_noninteractive_optional_default_mpiprocs_2(self):
        """
        Check that if is the specified value is zero, it means unspecified
        """
        from aiida.orm import Computer

        options_dict = generate_setup_options_dict({'label': 'computer_default_mpiprocs_2'})
        options_dict['mpiprocs-per-machine'] = 0
        options = generate_setup_options(options_dict)
        result = self.runner.invoke(setup_computer, options)

        self.assertIsNone(result.exception, result.output[-1000:])

        new_computer = Computer.get(options_dict['label'])
        self.assertIsInstance(new_computer, Computer)
        self.assertIsNone(new_computer.get_default_mpiprocs_per_machine())

    def test_noninteractive_optional_default_mpiprocs_3(self):
        """
        Check that it fails for a negative number of mpiprocs
        """
        options_dict = generate_setup_options_dict({'label': 'computer_default_mpiprocs_3'})
        options_dict['mpiprocs-per-machine'] = -1
        options = generate_setup_options(options_dict)
        result = self.runner.invoke(setup_computer, options)

        self.assertIsInstance(result.exception, SystemExit)
        self.assertIn("mpiprocs_per_machine, must be positive", result.output)

    def test_noninteractive_wrong_transport_fail(self):
        """
        Check that if fails as expected for an unknown transport
        """
        options_dict = generate_setup_options_dict(replace_args={'label': 'fail_computer'})
        options_dict['transport'] = 'unknown_transport'
        options = generate_setup_options(options_dict)
        result = self.runner.invoke(setup_computer, options)
        #import traceback
        #traceback.print_tb(result.exc_info[2])
        self.assertIsInstance(result.exception, SystemExit)
        self.assertIn("'unknown_transport' is not valid", result.output)

    def test_noninteractive_wrong_scheduler_fail(self):
        """
        Check that if fails as expected for an unknown transport
        """
        options_dict = generate_setup_options_dict(replace_args={'label': 'fail_computer'})
        options_dict['scheduler'] = 'unknown_scheduler'
        options = generate_setup_options(options_dict)
        result = self.runner.invoke(setup_computer, options)

        self.assertIsInstance(result.exception, SystemExit)
        self.assertIn("'unknown_scheduler' is not valid", result.output)

    def test_noninteractive_invalid_shebang_fail(self):
        """
        Check that if fails as expected for an unknown transport
        """
        options_dict = generate_setup_options_dict(replace_args={'label': 'fail_computer'})
        options_dict['shebang'] = '/bin/bash'  # Missing #! in front
        options = generate_setup_options(options_dict)
        result = self.runner.invoke(setup_computer, options)

        self.assertIsInstance(result.exception, SystemExit)
        self.assertIn("The shebang line should start with", result.output)

    def test_noninteractive_invalid_mpirun_fail(self):
        """
        Check that if fails as expected for an unknown transport
        """
        options_dict = generate_setup_options_dict(replace_args={'label': 'fail_computer'})
        options_dict['mpirun-command'] = 'mpirun -np {unknown_key}'
        options = generate_setup_options(options_dict)
        result = self.runner.invoke(setup_computer, options)

        self.assertIsInstance(result.exception, SystemExit)
        self.assertIn("unknown replacement field 'unknown_key'", str(result.output))


class TestVerdiComputerConfigure(AiidaTestCase):

    def setUp(self):
        """Prepare computer builder with common properties."""
        from aiida.orm.backend import construct_backend
        from aiida.control.computer import ComputerBuilder
        self.backend = construct_backend()
        self.user = self.backend.users.get_automatic_user()
        self.runner = CliRunner()
        self.comp_builder = ComputerBuilder(label='test_comp_setup')
        self.comp_builder.hostname = 'localhost'
        self.comp_builder.description = 'Test Computer'
        self.comp_builder.enabled = True
        self.comp_builder.scheduler = 'direct'
        self.comp_builder.work_dir = '/tmp/aiida'
        self.comp_builder.prepend_text = ''
        self.comp_builder.append_text = ''
        self.comp_builder.mpiprocs_per_machine = 8
        self.comp_builder.mpirun_command = 'mpirun'
        self.comp_builder.shebang = '#!xonsh'

    def test_top_help(self):
        """Test help option of verdi computer configure."""
        result = self.runner.invoke(computer_configure, ['--help'], catch_exceptions=False)
        self.assertIn('ssh', result.output)
        self.assertIn('local', result.output)

    def test_reachable(self):
        """Test reachability of top level and sub commands."""
        import subprocess as sp
        output = sp.check_output(['verdi', 'computer', 'configure', '--help'])
        sp.check_output(['verdi', 'computer', 'configure', 'local', '--help'])
        sp.check_output(['verdi', 'computer', 'configure', 'ssh', '--help'])
        sp.check_output(['verdi', 'computer', 'configure', 'show', '--help'])

    def test_local_ni_empty(self):
        """
        Test verdi computer configure local <comp>

        Test twice, with comp setup for local or ssh.

         * with computer setup for local: should succeed
         * with computer setup for ssh: should fail
        """
        self.comp_builder.label = 'test_local_ni_empty'
        self.comp_builder.transport = 'local'
        comp = self.comp_builder.new()
        comp.store()

        result = self.runner.invoke(computer_configure, ['local', comp.label, '--non-interactive'], catch_exceptions=False)
        self.assertTrue(comp.is_user_configured(self.user), msg=result.output)

        self.comp_builder.label = 'test_local_ni_empty_mismatch'
        self.comp_builder.transport = 'ssh'
        comp_mismatch = self.comp_builder.new()
        comp_mismatch.store()
        result = self.runner.invoke(computer_configure, ['local', comp_mismatch.label, '--non-interactive'], catch_exceptions=False)
        self.assertIsNotNone(result.exception)
        self.assertIn('ssh', result.output)
        self.assertIn('local', result.output)

    def test_local_interactive(self):
        self.comp_builder.label = 'test_local_interactive'
        self.comp_builder.transport = 'local'
        comp = self.comp_builder.new()
        comp.store()

        result = self.runner.invoke(computer_configure, ['local', comp.label], input='\n', catch_exceptions=False)
        self.assertTrue(comp.is_user_configured(self.user), msg=result.output)

    def test_ssh_ni_empty(self):
        """
        Test verdi computer configure ssh <comp>

        Test twice, with comp setup for ssh or local.

         * with computer setup for ssh: should succeed
         * with computer setup for local: should fail
        """
        self.comp_builder.label = 'test_ssh_ni_empty'
        self.comp_builder.transport = 'ssh'
        comp = self.comp_builder.new()
        comp.store()

        result = self.runner.invoke(computer_configure, ['ssh', comp.label, '--non-interactive'], catch_exceptions=False)
        self.assertTrue(comp.is_user_configured(self.user), msg=result.output)

        self.comp_builder.label = 'test_ssh_ni_empty_mismatch'
        self.comp_builder.transport = 'local'
        comp_mismatch = self.comp_builder.new()
        comp_mismatch.store()
        result = self.runner.invoke(computer_configure, ['ssh', comp_mismatch.label, '--non-interactive'], catch_exceptions=False)
        self.assertIsNotNone(result.exception)
        self.assertIn('local', result.output)
        self.assertIn('ssh', result.output)

    def test_ssh_ni_username(self):
        """Test verdi computer configure ssh <comp> --username=<username>."""
        self.comp_builder.label ='test_ssh_ni_username'
        self.comp_builder.transport = 'ssh'
        comp = self.comp_builder.new()
        comp.store()

        username = 'TEST'
        result = self.runner.invoke(computer_configure, ['ssh', comp.label, '--non-interactive', '--username={}'.format(username)], catch_exceptions=False)
        self.assertTrue(comp.is_user_configured(self.user), msg=result.output)
        self.assertEqual(self.backend.authinfos.get(comp, self.user).get_auth_params()['username'], username)

    def test_show(self):
        """Test verdi computer configure show <comp>."""
        self.comp_builder.label ='test_show'
        self.comp_builder.transport = 'ssh'
        comp = self.comp_builder.new()
        comp.store()

        result = self.runner.invoke(computer_configure, ['show', comp.label], catch_exceptions=False)

        result = self.runner.invoke(computer_configure, ['show', comp.label, '--defaults'], catch_exceptions=False)
        self.assertIn('* username', result.output)

        result = self.runner.invoke(computer_configure, ['show', comp.label, '--defaults', '--as-option-string'], catch_exceptions=False)
        self.assertIn('--username=', result.output)

        config_cmd = ['ssh', comp.label, '--non-interactive']
        config_cmd.extend(result.output.replace("'", '').split(' '))
        result_config = self.runner.invoke(computer_configure, config_cmd, catch_exceptions=False)
        self.assertTrue(comp.is_user_configured(self.user), msg=result_config.output)

        result_cur = self.runner.invoke(computer_configure, ['show', comp.label, '--as-option-string'], catch_exceptions=False)
        self.assertIn('--username=', result.output)
        self.assertEqual(result_cur.output, result.output)


class TestVerdiComputerCommands(AiidaTestCase):
    """Testing verdi computer commands.

    Testing everything besides `computer setup`.
    """

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """Create a new computer> I create a new one because I want to configure it and I don't want to
        interfere with other tests"""
        super(TestVerdiComputerCommands, cls).setUpClass(*args, **kwargs)
        from aiida.orm import Computer
        cls.computer_name = "comp_cli_test_computer"
        cls.comp = Computer(
            name=cls.computer_name,
            hostname='localhost',
            transport_type='local',
            scheduler_type='direct',
            workdir='/tmp/aiida')
        cls.comp.store()

    def setUp(self):
        """
        Prepare the computer and user
        """
        from aiida.control.computer import configure_computer

        self.user = self.backend.users.get_automatic_user()

        # I need to configure the computer here; being 'local',
        # there should not be any options asked here
        configure_computer(self.comp)

        assert self.comp.is_user_configured(self.user), "There was a problem configuring the test computer"
        self.runner = CliRunner()


    def test_enable_disable_globally(self):
        """
        Test if enabling and disabling a computer has the intended effect.
        Note I have to do it three times, because if because of a bug
        'enable' is a no-op and the computer was already enabled, the
        test would pass.
        """

        def enable_disable_globally_loop(self, user=None, user_enabled_state=True):
            result = self.runner.invoke(enable_computer, [str(self.comp.label)])
            self.assertIsNone(result.exception)
            self.assertTrue(self.comp.is_enabled())
            """
            Change global state check if user states are affected
            """

            # Check that the change of global state did not affect the
            # per-user state
            if user is not None:
                if user_enabled_state:
                    self.assertTrue(self.comp.is_user_enabled(user))
                else:
                    self.assertFalse(self.comp.is_user_enabled(user))

            result = self.runner.invoke(disable_computer, [str(self.comp.label)])
            self.assertIsNone(result.exception)
            self.assertFalse(self.comp.is_enabled())

            # Check that the change of global state did not affect the
            # per-user state
            if user is not None:
                if user_enabled_state:
                    self.assertTrue(self.comp.is_user_enabled(user))
                else:
                    self.assertFalse(self.comp.is_user_enabled(user))

            result = self.runner.invoke(enable_computer, [str(self.comp.label)])
            self.assertIsNone(result.exception)
            self.assertTrue(self.comp.is_enabled())

            # Check that the change of global state did not affect the
            # per-user state
            if user is not None:
                if user_enabled_state:
                    self.assertTrue(self.comp.is_user_enabled(user))
                else:
                    self.assertFalse(self.comp.is_user_enabled(user))

        ## Start of actual tests
        result = self.runner.invoke(enable_computer,
                                    ['--only-for-user={}'.format(self.user_email),
                                     str(self.comp.label)])
        self.assertIsNone(result.exception, msg="Error, output: {}".format(result.output))    #.stdout, result.stderr))
        self.assertTrue(self.comp.is_user_enabled(self.user))
        # enable and disable the computer globally as well
        enable_disable_globally_loop(self, self.user, user_enabled_state=True)

        result = self.runner.invoke(disable_computer,
                                    ['--only-for-user={}'.format(self.user_email),
                                     str(self.comp.label)])
        self.assertIsNone(result.exception, msg="Error, output: {}".format(result.output))    #.stdout, result.stderr))
        self.assertFalse(self.comp.is_user_enabled(self.user))
        # enable and disable the computer globally as well
        enable_disable_globally_loop(self, self.user, user_enabled_state=False)

        result = self.runner.invoke(enable_computer,
                                    ['--only-for-user={}'.format(self.user_email),
                                     str(self.comp.label)])
        self.assertIsNone(result.exception, msg="Error, output: {}".format(result.output))    #.stdout, result.stderr))
        self.assertTrue(self.comp.is_user_enabled(self.user))
        # enable and disable the computer globally as well
        enable_disable_globally_loop(self, self.user, user_enabled_state=True)

    def test_computer_test(self):
        """
        Test if the 'verdi computer test' command works

        It should work as it is a local connection
        """
        # Testing the wrong computer will fail
        result = self.runner.invoke(computer_test, ['non-existent-computer'])
        # An exception should arise
        self.assertIsNotNone(result.exception)

        # Testing the right computer should pass locally
        result = self.runner.invoke(computer_test, ['comp_cli_test_computer'])
        # No exceptions should arise
        self.assertIsNone(result.exception)

    def test_computer_list(self):
        """
        Test if 'verdi computer list' command works
        """
        # Check the vanilla command works
        result = self.runner.invoke(computer_list, [])
        # No exceptions should arise
        self.assertIsNone(result.exception)
        # Something should be printed to stdout
        self.assertIsNotNone(result.output)

        # Check all options run
        for opt in ['-o', '--only-usable', '-p', '--parsable', '-a', '--all-comps']:
            result = self.runner.invoke(computer_list, [opt])
            # No exceptions should arise
            self.assertIsNone(result.exception)
            # Something should be printed to stdout
            self.assertIsNotNone(result.output)

    def test_computer_show(self):
        """
        Test if 'verdi computer show' command works
        """
        result = self.runner.invoke(computer_list, ['-p'])

        # See if we can display info about the test computer.
        result = self.runner.invoke(computer_show, ['comp_cli_test_computer'])

        # No exceptions should arise
        self.assertIsNone(result.exception)
        # Something should be printed to stdout
        self.assertIsNotNone(result.output)

        # See if a non-existent computer will raise an error.
        result = self.runner.invoke(computer_show, 'non_existent_computer_name')
        # Exceptions should arise
        self.assertIsNotNone(result.exception)

    def test_computer_rename(self):
        """
        Test if 'verdi computer rename' command works
        """
        from aiida.orm.computer import Computer as AiidaOrmComputer
        from aiida.common.exceptions import NotExistent

        # See if the command complains about not getting an invalid computer
        options = ['not_existent_computer_name']
        result = self.runner.invoke(computer_rename, options)
        # Exception should be raised
        self.assertIsNotNone(result.exception)

        # See if the command complains about not getting both names
        options = ['comp_cli_test_computer']
        result = self.runner.invoke(computer_rename, options)
        # Exception should be raised
        self.assertIsNotNone(result.exception)

        # The new name must be different to the old one
        options = ['comp_cli_test_computer', 'comp_cli_test_computer']
        result = self.runner.invoke(computer_rename, options)
        # Exception should be raised
        self.assertIsNotNone(result.exception)

        # Change a computer name successully.
        options = ['comp_cli_test_computer', 'renamed_test_computer']
        result = self.runner.invoke(computer_rename, options)
        # Exception should be not be raised
        self.assertIsNone(result.exception)

        # Check that the name really was changed
        # The old name should not be available
        with self.assertRaises(NotExistent):
            AiidaOrmComputer.get('comp_cli_test_computer')
        # The new name should be avilable
        try:
            AiidaOrmComputer.get('renamed_test_computer')
        except NotExistent:
            assertTrue(False)

        # Now change the name back
        options = ['renamed_test_computer', 'comp_cli_test_computer']
        result = self.runner.invoke(computer_rename, options)
        # Exception should be not be raised
        self.assertIsNone(result.exception)

        # Check that the name really was changed
        # The old name should not be available
        with self.assertRaises(NotExistent):
            AiidaOrmComputer.get('renamed_test_computer')
        # The new name should be avilable
        try:
            AiidaOrmComputer.get('comp_cli_test_computer')
        except NotExistent:
            assertTrue(False)

    def test_computer_delete(self):
        """
        Test if 'verdi computer delete' command works
        """
        from aiida.orm.computer import Computer as AiidaOrmComputer
        from aiida.common.exceptions import NotExistent

        # Setup a computer to delete during the test
        comp = AiidaOrmComputer(
            name='computer_for_test_delete',
            hostname='localhost',
            transport_type='local',
            scheduler_type='direct',
            workdir='/tmp/aiida')
        comp.store()

        # See if the command complains about not getting an invalid computer
        options = ['non_existent_computer_name']
        result = self.runner.invoke(computer_delete, options)
        # Exception should be raised
        self.assertIsNotNone(result.exception)

        # Delete a computer name successully.
        options = ['computer_for_test_delete']
        result = self.runner.invoke(computer_delete, options)
        # Exception should be not be raised
        self.assertIsNone(result.exception)
        # Check that the computer really was deleted
        with self.assertRaises(NotExistent):
            AiidaOrmComputer.get('computer_for_test_delete')
