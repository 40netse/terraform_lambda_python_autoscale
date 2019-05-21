access_key = ""
secret_key = ""

aws_region                 = "us-east-1"
customer_prefix            = "asg-mdw"
environment                = "stage"
availability_zone1         = "us-east-1a"
availability_zone2         = "us-east-1b"
vpc_id                     = "vpc-0965cb963ac631678"
public1_subnet_id          = "subnet-05e9c0faddb524065"
public2_subnet_id          = "subnet-0476296f77c7e7792"
private1_subnet_id         = "subnet-0c7f21f6cada96541"
private2_subnet_id         = "subnet-0448a5c4b8c2dd2f2"
/*
vpc_cidr                   = "10.0.0.0/16"
public_subnet_cidr_1       = "10.0.0.0/24"
private_subnet_cidr_1      = "10.0.1.0/24"
public_subnet_cidr_2       = "10.0.2.0/24"
private_subnet_cidr_2      = "10.0.3.0/24"
*/
keypair                    = "Londonkey"
max_size                   = 5
min_size                   = 0
desired                    = 0
cidr_for_access            = "0.0.0.0/0"
endpoint_instance_type     = "t2.micro"
fortigate_instance_type     = "t2.small"
public_ip                  = true
sns_topic                  = "fgtautoscale-sns"
api_gateway_url            = "https://0azjhuaa5e.execute-api.us-east-1.amazonaws.com/dev/sns"
