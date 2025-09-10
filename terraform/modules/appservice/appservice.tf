resource "azurerm_service_plan" "plan" {
  name                = "${var.application_type}-plan"
  resource_group_name = var.resource_group_name
  location            = var.location
  os_type             = var.app_service_os_type  # "Linux"
  sku_name            = var.app_service_sku      # "S1"
}

resource "azurerm_linux_web_app" "app" {
  name                = var.app_service_name
  resource_group_name = var.resource_group_name
  location            = var.location
  service_plan_id     = azurerm_service_plan.plan.id

  site_config {
    application_stack { node_version = "18-lts" } # ستاك خفيف؛ النشر Zip يعمل
  }

  app_settings = {
    WEBSITE_RUN_FROM_PACKAGE = "1"
  }
}

output "app_default_hostname" {
  value = azurerm_linux_web_app.app.default_hostname
}
