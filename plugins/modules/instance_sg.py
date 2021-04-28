#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.basic import AnsibleModule
__metaclass__ = type
from proxmoxer import ProxmoxAPI
import requests

DOCUMENTATION = r'''
---
module: proxmox_sg

short_description: This is a module to assign security groups to instances in Proxmox.

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: |
    This module requires that you install the proxmoxer python module on the host you run it from.
    It will apply the security groups to the instances you specify and will REMOVE any other security groups
    the instance might have. 

options:
    security_groups:
        description: This is a list of security groups to apply to the instance 
        required: false
        type: list
    vmids:
        description: A list of hosts to apply those security groups to. 
        required: true
        type: list
    
author:
    - Daniel Podwysocki (@danielpodwysocki)
'''

EXAMPLES = r'''


- name: Assign a security group to an instance by providing a vmid
  danielpodwysocki.proxmox.assign_sg:
    security_group: sg_ssh
    vmids:
      - 101
      
- name: Assign a security group to multiple instances
  danielpodwysocki.proxmox.assign_sg:
    security_group: sg_ssh
    vmids:
      - 101
      - 102


- name: Unassign all security groups from instances contained in the list
  danielpodwysocki.proxmox.assign_sg:
    vmids:
      - 101
      - 102
      - 103
        
'''


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        security_group=dict(type='str', required=True),
        nodes=dict(type='list', required=False, elements='dict')
        instances=dict(type='list', required=False, elements='dict')
    )

    result = dict(
        changed=False
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(**result)
        
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
