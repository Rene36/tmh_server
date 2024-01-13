terraform {
  required_providers {
    opennebula = {
      source  = "opennebula/opennebula"
      version = "1.1.1"
    }
  }
}

provider "opennebula" {
  username      = var.ON_USERNAME
  password      = var.ON_PASSWD
  endpoint      = "http://xml-rpc.cloud.dis.cit.tum.de"
  flow_endpoint = "http://oneflow.cloud.dis.cit.tum.de"
  insecure      = true
}

resource "opennebula_virtual_machine" "client" {
  count = var.ON_VM_COUNT
  name        = "test_${count.index}"
  description = "Test VM"
  cpu         = var.CPU_CORES
  vcpu        = var.CPU_CORES
  memory      = var.MEMORY
  group       = var.ON_GROUP
  template_id = 118

  tags = {
    machine_count = count.index
  }

  disk {
    image_id = 41
    driver   = "qcow2"
    size     = var.DISK_SIZE # MB
    target   = "vda"
  }

  # THIS IS NEW. We use the password to attach our NAS.
  context = {
    RBG_PASSWORD = var.ON_PASSWD
  }

}

# This creates a terminal output with the IPs your VMs will have.
output "clients" {
  value = opennebula_virtual_machine.client.*.ip
}
