variable "ON_USERNAME" {
  description = "OpenNebula Username"
  type        = string
  default     = ""
}

variable "ON_PASSWD" {
  description = "OpenNebula Username"
  type        = string
  default     = ""
  sensitive   = true
}

variable "ON_GROUP" {
  # This is the group your supervisor assigned you to in OpenNebula.
  description = "OpenNebula Group"
  type        = string
  default     = ""
}

variable "ON_VM_COUNT" {
  description = "Number of VMs to spawn"
  type        = number
  # Be mindful with our resources!
  default     = 1
}

variable "CPU_CORES" {
  description = "CPU cores per VM"
  type        = number
  default     = 4
}

variable "MEMORY" {
  description = "Memory (RAM) per VM"
  type        = number
  default     = 6144 # 4GB + 2GB for hypervisor guest space reservation. Your VM will have 4GB of memory.
}

variable "DISK_SIZE" {
  description = "Disk size per VM"
  type        = number
  # Never use more storage on a regular VM. We will mount our NAS for you in the VM. For GPU nodes see our wiki. There,
  # you might be allowed to use more local disk.
  default     = 30720
}

variable "EXPERIMENT_NAME" {
  description = "Your experiment name"
  type        = string
  default     = "example"
}
