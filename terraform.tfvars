access_key = ""
secret_key = ""

aws_region                 = "us-east-1"
customer_prefix            = "asg-concur"
availability_zone1         = "us-east-1a"
availability_zone2         = "us-east-1b"
vpc_cidr                   = "10.0.0.0/16"
public_subnet_cidr_1       = "10.0.0.0/24"
private_subnet_cidr_1      = "10.0.1.0/24"
public_subnet_cidr_2       = "10.0.2.0/24"
private_subnet_cidr_2      = "10.0.3.0/24"
keypair                    = "kp-poc-common"
max_size                   = 5
min_size                   = 0
desired                    = 0
cidr_for_access            = "0.0.0.0/0"
endpoint_instance_type     = "t2.micro"
public_ip                  = true
lambda_name                = "handler"
lambda_description         = "Fortigate Autoscale Lambda Function"
lambda_handler             = "lambda_handler.handler"
lambda_runtime             = "python2.7"
lambda_package_path        = "./build/functions.zip"
sns_topic                  = "fgtautoscale-sns"
certificate_arn            = " arn:aws:acm:us-east-1:730386877786:certificate/88ff4e36-95c2-435c-a9a4-581acf12f037"

