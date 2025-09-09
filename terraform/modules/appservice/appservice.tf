resource "azurerm_service_plan" "test" {
  name                = "${var.application_type}-${var.resource_type}"
  location            = "${var.location}"
  resource_group_name = "${var.resource_group}"

  # بدّل من F1 (Free) إلى B1 (Basic) لتفادي مشكلة الكوتا
  os_type  = "Linux"
  sku_name = "B1"
}

resource "azurerm_linux_web_app" "test" {
  name                = "${var.application_type}-${var.resource_type}"
  location            = "${var.location}"
  resource_group_name = "${var.resource_group}"
  service_plan_id     = azurerm_service_plan.test.id

  app_settings = {
    "WEBSITE_RUN_FROM_PACKAGE" = 0
  }

  site_config {
    always_on = false   # B1 يسمح بتعطيل AlwaysOn
  }
}
