variable "resource_group_name" { type = string }
variable "location"            { type = string }

variable "virtual_network_name" { type = string }
variable "address_space"        { type = list(string) }
variable "address_prefix_test"  { type = string }