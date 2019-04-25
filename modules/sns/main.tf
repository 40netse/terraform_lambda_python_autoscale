provider "aws" {
  access_key    = "${var.access_key}"
  secret_key    = "${var.secret_key}"
  region        = "${var.aws_region}"
}


data "aws_iam_policy_document" "sns-topic-policy" {
  policy_id = "__default_policy_ID"

  statement {
    sid = "__default_statement_ID"
    actions = [
      "SNS:*"
    ]
    effect = "Allow"
    resources = ["*"]
    principals = {
      type = "AWS"
      identifiers = ["*"]
    }
  }
}


resource "aws_sns_topic" "sns_asg" {
  name = "${var.customer_prefix}-${var.environment}-${var.sns_topic}-topic"
}
/*
resource "aws_sns_topic_policy" "sns_topic_policy" {
  arn    = "${aws_sns_topic.sns_asg.arn}"
  policy = "${data.aws_iam_policy_document.sns-topic-policy.json}"
}
*/

resource "aws_sns_topic_subscription" "sns_subscription" {
  topic_arn = "${aws_sns_topic.sns_asg.arn}"
  protocol = "lambda"
  endpoint = "${var.notification_arn}"
}

resource "aws_lambda_permission" "with_sns" {
    statement_id = "AllowExecutionFromSNS"
    action = "lambda:InvokeFunction"
    function_name = "${var.notification_arn}"
    principal = "sns.amazonaws.com"
    source_arn = "${aws_sns_topic.sns_asg.arn}"
}
