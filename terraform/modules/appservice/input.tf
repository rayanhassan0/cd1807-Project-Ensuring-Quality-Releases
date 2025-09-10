variable "resource_group_name" { type = string }
variable "location"            { type = string }

variable "application_type"    { type = string } # prefix لأسماء الخطة
variable "app_service_name"    { type = string }
variable "app_service_sku"     { type = string } # مثال: S1
variable "app_service_os_type" { type = string } # مثال: Linux
