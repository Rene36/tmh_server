EXPERIMENT_NAME = "example"
ON_USERNAME     = "ABCD"              # THIS IS YOUR USERNAME (THE SAME YOU LOGIN WITH ON THE WEB)
ON_PASSWD       = "ABCD"              # THIS IS YOUR PASSWORD FOR THAT USER
ON_GROUP        = "ABCD"              # This is the group your advisor assigned you to. See the OpenNebula GUI, top right when clicking on your username.
ON_VM_COUNT     = 1                   # Number of VMs to spawn on OpenNebula. Be mindful with our resources!
CPU_CORES       = 4
MEMORY          = 6144                # MB; 4GB VM + 2GB for the hypervisor guest space reservation. You VM will have 4 GB of memory.
DISK_SIZE       = 30720               # MB; Never use a larger size.
