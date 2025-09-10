terraform {
  required_version = ">= 1.2.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.110"
    }
  }
}

provider "azurerm" {
  features {}
  # المصادقة تجي من Service Connection في Azure Pipelines (ARM_* env vars)
}

# نستخدم الـ RG الموجود مسبقًا (الاسم جاي من tfvars)
data "azurerm_resource_group" "rg" {
  name = var.resource_group_name
}

# --------- Network module ----------
module "network" {
  source              = "./modules/network"
  resource_group_name = data.azurerm_resource_group.rg.name
  location            = var.location

  virtual_network_name = var.virtual_network_name
  address_space        = var.address_space
  address_prefix_test  = var.address_prefix_test
}

# --------- App Service module ----------
module "appservice" {
  source              = "./modules/appservice"
  resource_group_name = data.azurerm_resource_group.rg.name
  location            = var.location

  application_type    = var.application_type
  app_service_name    = var.app_service_name
  app_service_sku     = var.app_service_sku
  app_service_os_type = var.app_service_os_type
}

output "app_default_hostname" {
  value = module.appservice.app_default_hostname
}
#تجربه 