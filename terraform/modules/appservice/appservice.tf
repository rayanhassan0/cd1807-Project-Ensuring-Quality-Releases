resource "azurerm_service_plan" "test" {
  name                = "${var.application_type}-${var.resource_type}"
  location            = "${var.location}"
  resource_group_name = "${var.resource_group}"
  os_type             = "Linux"
  sku_name            = "B1"   # <-- بدّلناها من F1 إلى B1 لأن F1 ما يدعم Linux
}

resource "azurerm_linux_web_app" "test" {
  name                = "${var.application_type}-${var.resource_type}"
  location            = "${var.location}"
  resource_group_name = "${var.resource_group}"
  service_plan_id     = azurerm_service_plan.test.id

  app_settings = {
    "WEBSITE_RUN_FROM_PACKAGE" = "0"  # app settings لازم تكون نصوص
  }

  site_config {
    always_on = false
  }
}
