variable "access_key" {}
variable "secret_key" {}

variable "aws_region" {
  description = "The AWS region to use"
  default = "us-east-1"
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
variable "customer_prefix" {
  description = "Customer Prefix to apply to all resources"
}

variable "environment" {
  description = "The Tag Environment in the S3 tag"
  default = "stage"
}
variable "availability_zone1" {
  description = "Availability Zone 1 for dual AZ VPC"
}

variable "availability_zone2" {
  description = "Availability Zone 2 for dual AZ VPC"
}
variable "vpc_cidr" {
    description = "CIDR for the whole VPC"
}

variable "public_subnet_cidr_1" {
    description = "CIDR for the Public Subnet"
}

variable "private_subnet_cidr_1" {
    description = "CIDR for the Private Subnet"
}

variable "public_subnet_cidr_2" {
    description = "CIDR for the Public Subnet"
}

variable "private_subnet_cidr_2" {
    description = "CIDR for the Private Subnet"
}
variable "keypair" {
  description = "Keypair for instances that support keypairs"
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
variable "cidr_for_access" {
  description = "CIDR to use for security group access"
}
variable "endpoint_instance_type" {
  description = "Instance type for endpoints in the private subnets"
}
variable "public_ip" {
  description = "Boolean to determine if endpoints should associate a public ip"
}
variable "sns_topic" {
  description = "SNS Topic"
}
