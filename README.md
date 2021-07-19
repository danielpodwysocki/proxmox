# proxmox

A collection of Ansible modules for managing Proxmox.

To install run:

```
ansible-galaxy collection install danielpodwysocki.proxmox
```
To update run:
```
ansible-galaxy collection install danielpodwysocki.proxmox -f
```

To view the documentation of a module run:
```
ansible-doc danielpodwysocki.proxmox.[module_name]
```

Current modules:
+ proxmox_sg - creates secruity groups and rules


Currently focusing on managing the proxmox firewall.

Manual testing workflow:

```
bash
cd workspace/ansible/
. venv/bin/activate
. hacking/env-setup
python -m ansible.modules.proxmox_sg ~/workspace/args.json 
```
The proxmox_sg module is symlinked to the checked out ansible repo (from within which we run the commands).

More details on that setup can be found in the Ansible docs: https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general.html
