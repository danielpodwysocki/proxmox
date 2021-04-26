# proxmox

An ansible collection of modules for managing Proxmox.

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
