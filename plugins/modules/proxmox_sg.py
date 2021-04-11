#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import proxmoxer
from proxmoxer import ProxmoxAPI
import requests

DOCUMENTATION = r'''
---
module: proxmox_sg

short_description: This is a module to create security groups and firewall rules within the Proxmox Virtual Environment

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: This module requires that you install the proxmoxer python module on the host you run it from.

options:
    name:
        description: This is the name of the security group you'll be creating.
        required: true
        type: str
    api_host:
        description: This is the proxmox node with the exposed API
        required: true
        type: str
    api_user:
        description: User that will be accessing the API, for example `root@pam` (@ specifies the auth backend)
        required: true
        type: str
    api_password:
        description: Password for the api user
        required: true
        type: str
    verify_ssl:
        description: A boolean that determines whether or not the ssl check should be skipped 
        required: false
        type: bool
        default: true
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
extends_documentation_fragment:
    - danielpodwysocki.proxmox.general

author:
    - Daniel Podwysocki (@danielpodwysocki)
'''

EXAMPLES = r'''
# Pass in a message
- name: Test with a message
  my_namespace.my_collection.my_test:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_namespace.my_collection.my_test:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_namespace.my_collection.my_test:
    name: fail me
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
    sample: 'hello world'
message:
    description: The output message that the test module generates.
    type: str
    returned: always
    sample: 'goodbye'
'''

from ansible.module_utils.basic import AnsibleModule

def rule_is_valid(rule):
    '''
    returns True if the rule posseses the necessary fields
    '''
    if 'action' not in rule or 'type' not in rule:
        return False
    else:
        return True

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        name=dict(type='str', required=True),
        comment=dict(type='str', required=False),
        api_password=dict(type='str', required=True, no_log=True),
        api_user=dict(type='str', required=True),
        api_host=dict(type='str', required=True),
        verify_ssl=dict(type='bool', required=False, default=True),
        rules=dict(type='list', required=False, elements='dict')

    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    result['original_message'] = module.params['name']
    result['message'] = 'goodbye'

    #determine if the group already exists
    proxmox = ProxmoxAPI(module.params['api_host'], user=module.params['api_user'],
                     password=module.params['api_password'], verify_ssl=module.params['verify_ssl'])
    security_groups = proxmox.cluster.firewall.groups.get()    
    
    #check if the sg exists, if it does set sg_exists to True
    sg_exists=False
    for sg in security_groups:
        if sg['group'] == module.params['name']:
           sg_exists = True
    #check if all the rules are valid, if not, fail the execution
    for rule in module.params['rules']:
        if not rule_is_valid(rule):
            module.fail_json(msg='The firewall rules were not correct', **result)

    #the result['changed'] defaults to False, if we're creating a group, make it True and then create the group
    if not sg_exists:
        result['changed'] = True
        proxmox.cluster.firewall.groups.create(group=module.params['name'])
        for rule in module.params['rules']:
            proxmox.cluster.firewall.groups(module.params['name']).create(action=rule['action'],type=rule['type'] ,group=module.params['name'])
            
    # else:
    #     rules = proxmox.cluster.firewall.rules.get()
    

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
