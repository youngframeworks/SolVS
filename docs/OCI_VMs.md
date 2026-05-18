# OCI VM Inventory (SolVS)

This file records the OCI VM references and SSH public keys used by the fleet.

- **SolOS Main**
  - Public IP: 130.162.196.147
  - Private IP: 10.0.0.119
  - Shape: VM.Standard.A1.Flex 4 vCPU / 24GB (ARM)
  - SSH public key: `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGNrV9qJ8sAs3AVpR2EjmaeglY6joJJHpDE7ty5DBaNS young@aistudio`

- **SolOS Node 1**
  - Public IP: 169.224.230.139
  - Private IP: 10.0.0.143
  - Shape: VM.Standard.A1.Flex 4 vCPU / 24GB (ARM)
  - SSH public key: `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFzoFGi0xlqMp8wolCcV87mCR7rC6d9SbhE6448pD+Dz solos-node-1`

- **SolOS Node 2**
  - Public IP: 152.69.188.3
  - Private IP: 10.0.0.213
  - Shape: VM.Standard.A1.Flex 4 vCPU / 24GB (ARM)
  - SSH public key: `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOS6fZvFLl4v3g95NjN61v7L08dzESQX9CerBY3IBsMK solos-node-2`

Notes:
- The SSH public keys are recorded here and in `config/oci_vms.json` for reference. To actually add the keys to a VM, either use the OCI console/Cloud-Init user-data, or append the public key to the target user's `~/.ssh/authorized_keys` on each VM.
- This file is informational; apply keys to the VMs using your usual provisioning or configuration management workflow.
