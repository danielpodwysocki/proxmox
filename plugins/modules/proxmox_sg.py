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
    rules:
        description: A list of rules, which themselves are dictionaries (see example). Rule's attributes follow the ones outlined in the proxmox api ('https://pve.proxmox.com/pve-docs/api-viewer/\#/cluster/firewall/groups/{group}')
    
author:
    - Daniel Podwysocki (@danielpodwysocki)
'''

EXAMPLES = r'''
- name: Create a security group without any rules
  danielpodwysocki.proxmox.proxmox_sg:
    name: empty_sg
    api_user: {{ api_user }}
    api_password: {{ api_password }}
    api_host: {{ api_host }}
    verify_ssl: False    

- name: Create a security group with a rule allowing SSH access
  danielpodwysocki.proxmox.proxmox_sg:
    name: ssh_sg
    api_user: {{ api_user }}
    api_password: {{ api_password }}
    api_host: {{ api_host }}
    verify_ssl: False
    rules:
      - enable: 1
        type: IN
        action: ACCEPT
        dport: 22

'''


def rule_is_valid(rule):
    '''
    returns True if the rule posseses the necessary fields
    '''
    if 'action' not in rule or 'type' not in rule:
        return False
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

    result = dict(
        changed=False
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )


#determine if the group already exists
    proxmox = ProxmoxAPI(module.params['api_host'], user=module.params['api_user'],
                     password=module.params['api_password'], verify_ssl=module.params['verify_ssl'])
    security_groups = proxmox.cluster.firewall.groups.get()    
    rules_existing = []


#check if the sg exists, if it does set sg_exists to True
    sg_exists = False
    rules_defined = []
    rules_changed = []
    for sg in security_groups:
        if sg['group'] == module.params['name']:
            sg_exists = True
            rules_existing = proxmox.cluster.firewall.groups(module.params['name']).get()

    if not sg_exists:
        result['changed'] = True

#clean the rules from the digest
    clean_rules(rules_existing)
    if 'rules' in module.params:
        rules_defined = pad_rules(module.params['rules'])
#check if all the rules passed to the module are valid, if not, fail the execution
        for rule in module.params['rules']:
            if not rule_is_valid(rule):
                module.fail_json(msg='The firewall rules were not correct', **result)

        #check if the rulesets are identical
        rules_changed = rulesets_diff(rules_existing, rules_defined)
        if rules_changed:
            result['changed'] = True

    #Return the status of changes if we're in check mode
    if module.check_mode:
        module.exit_json(**result)
        
  
    #if the security group doesn't already exist, create it. Then create all the corresponding rules
    if not sg_exists:
        proxmox.cluster.firewall.groups.create(group=module.params['name'])
        for rule in rules_defined:
            proxmox.cluster.firewall.groups(module.params['name']).create(**rule)

    elif rules_changed:
        for rule in rules_changed:
            #if a rule on that position no longer exists, delete it.
            if rule > len(rules_defined) - 1:
                proxmox.cluster.firewall.groups(module.params['name'])(rule).delete()
            #if a rule on that position doesn't exist, but it should, create it
            elif rule > len(rules_existing) -1:
                proxmox.cluster.firewall.groups(module.params['name']).create(**rules_defined[rule])
            #if a rule exists on that position, but is different, modify it
            else:
                proxmox.cluster.firewall.groups(module.params['name'])(str(rule)).set(**rules_defined[rule])


            module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
