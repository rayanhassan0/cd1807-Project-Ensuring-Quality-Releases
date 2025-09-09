# input.tf
variable "resource_group" {
  type = string
}

variable "location" {
  type    = string
  default = null
}
