variable "access_key" {}
variable "secret_key" {}

variable "aws_region" {
  description = "Provide the region to deploy the VPC in"
}
variable "ami_id" {
  description = "AMI ID of instances in the autoscale group"
}
variable "vpc_id" {
  description = "The VPC Id of the newly created VPC."
}
variable "instance_type" {
  description = "Instance type to launch from the autoscale group"
}
variable "subnet1_id" {
  description = "Provide the ID for the first public subnet"
}
variable "subnet2_id" {
  description = "Provide the ID for the first public subnet"
}
variable "security_group" {
  description = "Security Group for autoscale instances"
}
variable "instance1_id" {
  description = "Provide the ID for the first fgt instance"
}
variable "instance2_id" {
  description = "Provide the ID for the first fgt instance"
}
variable "key_name" {
  description = "Keyname to use for the autoscale instance"
}
variable "max_size" {
  description = "Max autoscale group size"
}
variable "min_size" {
  description = "Min autoscale group size"
}
variable "desired" {
  description = "Desired autoscale group size"
}
variable "customer_prefix" {
  description = "Customer Prefix to apply to all resources"
}

variable "environment" {
  description = "The Tag Environment NLB tag"
}
variable "autoscale_notifications_needed" {
  description = "autoscale notifications needed true/false"
}
variable "topic_arn" {
  description = "Topic ARN for Lifecycle Notifications"
}