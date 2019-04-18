
resource "aws_lambda_function" "lambda" {
  function_name    = "${var.name}"
  description      = "${var.description}"
  handler          = "${var.handler}"
  runtime          = "${var.runtime}"
  role             = "${aws_iam_role.iam_for_lambda.arn}"

  filename         = "${var.package_path}"
  source_code_hash = "${base64sha256(var.package_path)}"
}

resource "aws_iam_role" "iam_for_lambda" {
  name = "iam_for_lambda"
  path = "/"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

