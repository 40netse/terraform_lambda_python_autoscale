provider "aws" {
  access_key    = "${var.access_key}"
  secret_key    = "${var.secret_key}"
  region        = "${var.aws_region}"
}

resource "aws_launch_configuration" "asg_launch" {
  name            = "${var.customer_prefix}-${var.environment}-launch-configuration"
  image_id        = "${var.ami_id}"
  instance_type   = "${var.instance_type}"
  key_name        = "${var.key_name}"
  security_groups = ["${var.security_group}"]
}

resource "aws_autoscaling_group" "asg" {
  name                 = "${var.customer_prefix}-${var.environment}-autoscale"
  max_size             = "${var.max_size}"
  min_size             = "${var.min_size}"
  desired_capacity     = "${var.desired}"
  vpc_zone_identifier  = ["${var.subnet1_id}", "${var.subnet2_id}"]
  launch_configuration = "${aws_launch_configuration.asg_launch.name}"
  health_check_type    = "ELB"
  termination_policies = ["NewestInstance"]
}

resource "aws_autoscaling_policy" "scale-in-policy" {
  name               = "${var.customer_prefix}-${var.environment}-autoscale-in-policy"
  scaling_adjustment = -1
  adjustment_type = "ChangeInCapacity"
  autoscaling_group_name = "${aws_autoscaling_group.asg.name}"

}

resource "aws_autoscaling_policy" "scale-out-policy" {
  name                   = "${var.customer_prefix}-${var.environment}-autoscale-out-policy"
  scaling_adjustment     = 1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300
  autoscaling_group_name = "${aws_autoscaling_group.asg.name}"
}

resource "aws_cloudwatch_metric_alarm" "CPUAlarmLow" {
  alarm_name          = "${var.customer_prefix}-${var.environment}-cpulo-alarm"
  comparison_operator = "LessThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "300"
  statistic           = "Average"
  threshold           = "20"

  dimensions = {
    AutoScalingGroupName = "${aws_autoscaling_group.asg.name}"
  }

  alarm_description = "This metric monitors ec2 cpu utilization"
  alarm_actions     = ["${aws_autoscaling_policy.scale-in-policy.arn}"]
}

resource "aws_cloudwatch_metric_alarm" "CPUAlarmHigh" {
  alarm_name          = "${var.customer_prefix}-${var.environment}-cpuhi-alarm"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"

  dimensions = {
    AutoScalingGroupName = "${aws_autoscaling_group.asg.name}"
  }

  alarm_description = "This metric monitors ec2 cpu utilization"
  alarm_actions     = ["${aws_autoscaling_policy.scale-out-policy.arn}"]
}

resource "aws_autoscaling_notification" "asg-notification"{
  count                  = "${var.autoscale_notifications_needed == "true" ? 1 : 0}"
  group_names            = ["${aws_autoscaling_group.asg.name}"]
  notifications          = [ "autoscaling:EC2_INSTANCE_LAUNCH",
                             "autoscaling:EC2_INSTANCE_LAUNCH_ERROR",
                             "autoscaling:EC2_INSTANCE_TERMINATE",
                             "autoscaling:EC2_INSTANCE_TERMINATE_ERROR"
  ]
  topic_arn              = "${var.topic_arn}"
}

resource "aws_autoscaling_lifecycle_hook" "asg-lch"{
  count                  = "${var.autoscale_notifications_needed == "true" ? 1 : 0}"
  name                   = "${var.customer_prefix}-${var.environment}-lch"
  autoscaling_group_name = "${aws_autoscaling_group.asg.name}"
  default_result         = "ABANDON"
  heartbeat_timeout      = 500
  lifecycle_transition = ""
}

