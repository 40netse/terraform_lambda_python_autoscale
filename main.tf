
provider "aws" {
  region = "${var.aws_region}"
  access_key = "${var.access_key}"
  secret_key = "${var.secret_key}"
}

module "vpc" {
  source = "terraform_vpc"

  access_key                 = "${var.access_key}"
  secret_key                 = "${var.secret_key}"
  aws_region                 = "${var.aws_region}"
  environment                = "${var.environment}"
  customer_prefix            = "${var.customer_prefix}"
  availability_zone1         = "${var.availability_zone1}"
  availability_zone2         = "${var.availability_zone2}"
  vpc_cidr                   = "${var.vpc_cidr}"
  public_subnet_cidr_1       = "${var.public_subnet_cidr_1}"
  private_subnet_cidr_1      = "${var.private_subnet_cidr_1}"
  public_subnet_cidr_2       = "${var.public_subnet_cidr_2}"
  private_subnet_cidr_2      = "${var.private_subnet_cidr_2}"
}

module "endpoints" {
  source = "terraform_endpoints"

  access_key                 = "${var.access_key}"
  secret_key                 = "${var.secret_key}"
  aws_region                 = "${var.aws_region}"
  vpc_id                     = "${module.vpc.vpc_id}"
  private1_subnet_id         = "${module.vpc.private1_subnet_id}"
  private2_subnet_id         = "${module.vpc.private2_subnet_id}"
  keypair                    = "${var.keypair}"
  customer_prefix            = "${var.customer_prefix}"
  environment                = "${var.environment}"
  cidr_for_access            = "${var.cidr_for_access}"
  instance_type              = "${var.endpoint_instance_type}"
  public_ip                  = "${var.public_ip}"
  load_balancer_type         = "${var.load_balancer_type}"
}
