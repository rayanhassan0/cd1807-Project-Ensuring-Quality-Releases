variable "location"            { type = string }
variable "resource_group_name" { type = string }
variable "application_type"    { type = string }

# شبكة
variable "virtual_network_name" { type = string }
variable "address_space"        { type = list(string) }
variable "address_prefix_test"  { type = string }

# App Service
variable "app_service_name"    { type = string }  # لازم يطابق azure-pipelines.yaml
variable "app_service_sku"     { type = string }  # مثال: S1
variable "app_service_os_type" { type = string }  # مثال: Linux
