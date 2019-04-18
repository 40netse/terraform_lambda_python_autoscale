output "instance1_id" {
  value       = "${module.endpoint1.instance_id}"
  description = "Instance Id for endpoint 1"
}
output "instance1_key" {
  value = "${module.endpoint1.key_name}"
}
output "public1_ip" {
  value = "${module.endpoint1.public_ip}"
}
output "private1_ip" {
  value = "${module.endpoint1.private_ip}"
}
output "instance2_id" {
  value       = "${module.endpoint2.instance_id}"
  description = "Instance Id for endpoint 2"
}
output "instance2_key" {
  value = "${module.endpoint2.key_name}"
}
output "public2_ip" {
  value = "${module.endpoint2.public_ip}"
}
output "private2_ip" {
  value = "${module.endpoint2.private_ip}"
}
output "nlb_id" {
  value = "${module.nlb.nlb_id}"
}
output "alb_id" {
  value = "${module.nlb.alb_id}"
}
output "alb_dns" {
  value       = "${module.nlb.alb_dns}"
  description = "Application Load Balancer dns name"
}
output "nlb_dns" {
  value       = "${module.nlb.nlb_dns}"
  description = "Network Load Balancer dns name"
}
