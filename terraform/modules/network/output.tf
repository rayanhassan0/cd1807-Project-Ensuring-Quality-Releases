output "vnet_name" {
  value = azurerm_virtual_network.vnet.name
}

output "subnet_test_id" {
  value = azurerm_subnet.subnet_test.id
}