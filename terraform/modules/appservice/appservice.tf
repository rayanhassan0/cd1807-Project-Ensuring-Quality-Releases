resource "azurerm_service_plan" "test" {
  name                = "${var.application_type}-${var.resource_type}-plan"
  location            = var.location
  resource_group_name = var.resource_group
  os_type             = "Linux"
  sku_name            = "S1"
}

resource "azurerm_linux_web_app" "test" {
  name                = "${var.application_type}-${var.resource_type}-web"
  location            = var.location
  resource_group_name = var.resource_group
  service_plan_id     = azurerm_service_plan.test.id

  site_config {
    always_on = true
  }
}
