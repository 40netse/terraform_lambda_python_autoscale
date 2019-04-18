provider "aws" {
  access_key = "${var.access_key}"
  secret_key = "${var.secret_key}"
  region = "${var.aws_region}"
}

data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-bionic-18.04-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = ["099720109477"] # Canonical
}

module "ec2-sg" {
  source = "../modules/security_group"
  access_key           = "${var.access_key}"
  secret_key           = "${var.secret_key}"
  aws_region           = "${var.aws_region}"
  vpc_id               = "${var.vpc_id}"
  name                 = "${var.sg_name}"
  ingress_to_port         = 22
  ingress_from_port       = 0
  ingress_protocol        = "tcp"
  ingress_cidr_for_access = "0.0.0.0/0"
  egress_to_port          = 0
  egress_from_port        = 0
  egress_protocol         = "-1"
  egress_cidr_for_access = "0.0.0.0/0"
  customer_prefix      = "${var.customer_prefix}"
  environment          = "${var.environment}"
}

module "ec2-asg" {
  source = "../modules/autoscale"
  access_key                     = "${var.access_key}"
  secret_key                     = "${var.secret_key}"
  aws_region                     = "${var.aws_region}"
  vpc_id                         = "${var.vpc_id}"
  instance_type                  = "${var.instance_type}"
  ami_id                         = "${data.aws_ami.ubuntu.id}"
  subnet1_id                     = "${var.private1_subnet_id}"
  subnet2_id                     = "${var.private2_subnet_id}"
  security_group                 = "${module.ec2-sg.id}"
  key_name                       = "${var.keypair}"
  instance1_id                   = "${module.endpoint1.instance_id}"
  instance2_id                   = "${module.endpoint2.instance_id}"
  max_size                       = "${var.max_size}"
  min_size                       = "${var.min_size}"
  desired                        = "${var.desired}"
  customer_prefix                = "${var.customer_prefix}"
  environment                    = "${var.environment}"
  autoscale_notifications_needed = "false"
  topic_arn                      = ""
}

module "endpoint1" {
  source = "../modules/endpoints"
  access_key           = "${var.access_key}"
  secret_key           = "${var.secret_key}"
  aws_region           = "${var.aws_region}"
  ami_id               = "${data.aws_ami.ubuntu.id}"
  vpc_id               = "${var.vpc_id}"
  subnet_id            = "${var.private1_subnet_id}"
  keypair              = "${var.keypair}"
  cidr_for_access      = "${var.cidr_for_access}"
  customer_prefix      = "${var.customer_prefix}"
  environment          = "${var.environment}"
  instance_type        = "${var.instance_type}"
  instance_count       = "1"
  public_ip            = "${var.public_ip}"
  security_group       = "${module.ec2-sg.id}"
}

module "endpoint2" {
  source = "../modules/endpoints"
  access_key           = "${var.access_key}"
  secret_key           = "${var.secret_key}"
  aws_region           = "${var.aws_region}"
  ami_id               = "${data.aws_ami.ubuntu.id}"
  vpc_id               = "${var.vpc_id}"
  subnet_id            = "${var.private2_subnet_id}"
  keypair              = "${var.keypair}"
  cidr_for_access      = "${var.cidr_for_access}"
  customer_prefix      = "${var.customer_prefix}"
  environment          = "${var.environment}"
  instance_type        = "${var.instance_type}"
  instance_count       = "2"
  public_ip            = "${var.public_ip}"
  security_group       = "${module.ec2-sg.id}"
}

/*
module "nlb" {
  source               = "../modules/nlb"
  access_key           = "${var.access_key}"
  secret_key           = "${var.secret_key}"
  aws_region           = "${var.aws_region}"
  vpc_id               = "${var.vpc_id}"
  subnet1_id           = "${var.private1_subnet_id}"
  subnet2_id           = "${var.private2_subnet_id}"
  customer_prefix      = "${var.customer_prefix}"
  environment          = "${var.environment}"
  instance1_id         = "${module.endpoint1.instance_id}"
  instance2_id         = "${module.endpoint2.instance_id}"
}
*/