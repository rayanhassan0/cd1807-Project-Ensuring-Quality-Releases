resource "azurerm_service_plan" "test" {
  name                = "${var.name}-AppService-plan"
  resource_group_name = var.resource_group_name
  location            = var.location
  os_type             = var.os_type
  sku_name            = var.app_service_sku
}
