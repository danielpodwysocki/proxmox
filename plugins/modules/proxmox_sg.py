#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.basic import AnsibleModule
__metaclass__ = type
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
    sample: 'goodbye'ru
'''


def rule_is_valid(rule):
    '''
    returns True if the rule posseses the necessary fields
    '''
    if 'action' not in rule or 'type' not in rule:
        return False
    # if rule['action'] not in ['ACCEPT','REJECT','DROP']:
    #     return False
    return True


def pad_rules(rules):
    rules_padded = []
    for i, rule in enumerate(rules):
        rule['pos'] = i
        if 'enable' not in rule:
            rule['enable'] = 0
        rules_padded.append(rule) 


    return rules_padded


def clean_rules(rules):
    '''
    Takes in an array of rules (defined as dicts) and removes the digest key/val pair from every rule in it
    '''
    for rule in rules:
        rule.pop('digest')

def rulesets_diff(rules_existing, rules_defined):
    '''
    returns an arr with positions of rules that aren't identical to each other
    '''
    ret = []
    print(rules_existing)
    print(rules_defined)
    if len(rules_existing) == len(rules_defined):
        #we check if both dicts contain the key/val pairs, if not we add the pos of the rule to the list
        for rule_defined, rule_existing in zip(rules_defined, rules_existing):
            if rule_defined != rule_existing:
                ret.append(rule_defined['pos'])
    elif len(rules_existing) < len(rules_defined):
        for rule_defined, rule_existing in zip(rules_defined[:len(rules_existing)], rules_existing):
            if rule_defined != rule_existing:
                ret.append(rule_defined['pos'])

        for x in range(len(rules_existing), len(rules_defined)):
            ret.append(x)
    else:
        for rule_defined, rule_existing in zip(rules_defined, rules_existing[:len(rules_defined)]):
            if rule_defined != rule_existing:
                ret.append(rule_defined['pos'])

        for x in range(len(rules_defined), len(rules_existing)):
            ret.append(x)


    return ret


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
        supports_check_mode=True
    )


    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    result['original_message'] = module.params['name']
    result['message'] = 'goodbye'

    #determine if the group already exists
    proxmox = ProxmoxAPI(module.params['api_host'], user=module.params['api_user'],
                     password=module.params['api_password'], verify_ssl=module.params['verify_ssl'])
    security_groups = proxmox.cluster.firewall.groups.get()    
    rules_existing = []


    #check if the sg exists, if it does set sg_exists to True
    sg_exists = False
    rules_changed = False
    for sg in security_groups:
        if sg['group'] == module.params['name']:
            sg_exists = True
            rules_existing = proxmox.cluster.firewall.groups(module.params['name']).get()
        else:
            result['changed'] = True
        
    if not sg_exists:
        result['changed'] = True
    
    #clean the rules from the digest
    clean_rules(rules_existing)
    if 'rules' in module.params:
        #check if all the rules passed to the module are valid, if not, fail the execution
        for rule in module.params['rules']:
            if not rule_is_valid(rule):
                module.fail_json(msg='The firewall rules were not correct', **result)
        
        #check if the rulesets are identical
        if rulesets_diff(rules_existing, pad_rules(module.params['rules'])):
            result['changed'] = True
            rules_changed = True
    print(rulesets_diff(rules_existing, pad_rules(module.params['rules'])))
    
    #Return the status of changes if we're in check mode
    if module.check_mode:
        module.exit_json(**result)
        
  
    #if the security group doesn't already exist, create it. Then create all the corresponding rules
    if not sg_exists:
        proxmox.cluster.firewall.groups.create(group=module.params['name'])
        for rule in module.params['rules']:
            proxmox.cluster.firewall.groups(module.params['name']).create(action=rule['action'],type=rule['type'] ,group=module.params['name'])
            
    elif rules_changed:
        print('reconcile the rules changes')
    else:
        print('ok')
        

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
