variable "access_key" {}
variable "secret_key" {}

variable "aws_region" {
  description = "Provide the region to use"
}
variable "lambda_name" {
  description = "Lambda function for Fortigate Autoscaling"
}
variable "lambda_description" {
  description = "Fortigate Autoscale Lambda Function"
}
variable "lambda_handler" {
  description = "Lambda handler function"
}
variable "lambda_runtime" {
  description = "Runtime for the lambda function"
}
variable "lambda_package_path" {
  description = "Path to lambda zip file"
}
variable "vpc_id" {
  description = "VPC Id"
}
variable "public1_subnet_id" {
  description = "Provide the ID for first public subnet"
}
variable "public2_subnet_id" {
  description = "Provide the ID for 2nd public subnet"
}
variable "private1_subnet_id" {
  description = "Provide the ID for first public subnet"
}
variable "private2_subnet_id" {
  description = "Provide the ID for 2nd public subnet"
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
variable "keypair" {
  description = "Provide a keypair for accessing the FortiGate instance"
}
variable "customer_prefix" {
  description = "Customer Prefix to apply to all resources"
}
variable "environment" {
  description = "The Tag Environment in the S3 tag"
}
variable "cidr_for_access" {
  description = "CIDR to use for security group access"
}
variable "instance_type" {
  description = "Instance type for endpoints in the private subnets"
}
variable "public_ip" {
  description = "Associate Public IP Address"
}
variable "sg_name" {
  description = "Security Group Name for EC2 instances"
}
variable "sns_topic" {
  description = "SNS Topic"
}

