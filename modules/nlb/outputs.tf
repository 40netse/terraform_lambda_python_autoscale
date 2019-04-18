output "nlb_id" {
  value       = "${aws_lb.public_nlb.id}"
  description = "Network Load Balancer Id"
}
output "nlb_dns" {
  value       = "${aws_lb.public_nlb.dns_name}"
  description = "Network Load Balancer dns name"
}

