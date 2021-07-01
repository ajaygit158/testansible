# This function is not intended to be invoked directly. Instead it will be
# triggered by an orchestrator function.
# Before running this sample, please:
# - create a Durable orchestration function
# - create a Durable HTTP starter function
# - add azure-functions-durable to requirements.txt
# - run pip install -r requirements.txt

import logging
import json
import shutil
import os
import uuid
import requests
from ansible import context
from ansible.cli import CLI
from ansible.module_utils.common.collections import ImmutableDict
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.plugins.callback import CallbackBase
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager

# Create a callback plugin so we can capture the output
class ResultsCollectorJSONCallback(CallbackBase):
    """A sample callback plugin used for performing an action as results come in.

    If you want to collect all results into a single object for processing at
    the end of the execution, look into utilizing the ``json`` callback plugin
    or writing your own custom callback plugin.
    """

    def __init__(self, *args, **kwargs):
        super(ResultsCollectorJSONCallback, self).__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}

    def v2_runner_on_unreachable(self, result):
        host = result._host
        self.host_unreachable[host.get_name()] = result
        print(json.dumps({host.name: result._result}, indent=4))

    def v2_runner_on_ok(self, result, *args, **kwargs):
        """Print a json representation of the result.

        Also, store the result in an instance attribute for retrieval later
        """
        host = result._host
        self.host_ok[host.get_name()] = result
        print(json.dumps({host.name: result._result}, indent=4))

    def v2_runner_on_failed(self, result, *args, **kwargs):
        host = result._host
        self.host_failed[host.get_name()] = result
        print(json.dumps({host.name: result._result}, indent=4))

def main(name: str) -> str:
    playbookFileUrl = 'https://ajaythinkpadrmssa.blob.core.windows.net/testansible/testansible/v1/testansible.yml'
    host_list = ['10.0.0.4']
    print('Calling function')
    runPlaybook(playbookFileUrl, host_list)
    return f"Hello {name}!"

def runPlaybook(playbookFileUrl: str, host_list) -> str:
    loader = DataLoader()

    parentDir = os.getenv('HOME')
    workspaceDirName = uuid.uuid4().hex
    mode = 0o777
    path = os.path.join(parentDir, workspaceDirName)
    os.mkdir(path, mode)
    print("Directory '% s' created" % workspaceDirName)

    playbookFilePath = os.path.join(path, 'ansible_playbook.yml');
    r = requests.get(playbookFileUrl, allow_redirects=True)
    with open(playbookFilePath,'wb') as f:
        f.write(r.content)

    open(playbookFilePath, 'wb').write(r.content)

    sources = ','.join(host_list)

    results_callback = ResultsCollectorJSONCallback()

    context.CLIARGS = ImmutableDict(tags={}, listtags=False, listtasks=False, listhosts=False, syntax=False, connection='ssh', module_path=None, forks=100, remote_user='xxx', private_key_file=None, ssh_common_args=None, ssh_extra_args=None, sftp_extra_args=None, scp_extra_args=None, become=True, become_method='sudo', become_user='root', verbosity=True, check=False, start_at_task=None)

    inventory = InventoryManager(loader=loader, sources=sources)

    variable_manager = VariableManager(loader=loader, inventory=inventory)

    pbex = PlaybookExecutor(playbooks=[playbookFilePath], inventory=inventory, variable_manager=variable_manager, loader=loader, passwords={})

    pbex._tqm._stdout_callback = ResultsCollectorJSONCallback()

    try:
        results = pbex.run()
    finally:
        os.rmdir(path)
        if loader:
            loader.cleanup_all_tmp_files()

main('ajay')