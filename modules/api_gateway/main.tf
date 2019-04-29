provider "aws" {
  access_key    = "${var.access_key}"
  secret_key    = "${var.secret_key}"
  region        = "${var.aws_region}"
}

resource "aws_api_gateway_rest_api" "api" {
  name        = "${var.customer_prefix}-${var.environment}-rest-api"
  description = "Proxy to handle requests to our API"
  endpoint_configuration {
    types     = ["REGIONAL"]
  }
}

resource "aws_api_gateway_resource" "resource" {
  rest_api_id = "${aws_api_gateway_rest_api.api.id}"
  parent_id   = "${aws_api_gateway_rest_api.api.root_resource_id}"
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "proxy_root" {
  rest_api_id   = "${aws_api_gateway_rest_api.api.id}"
  resource_id   = "${aws_api_gateway_resource.resource.id}"
  http_method   = "ANY"
  authorization = "NONE"

  #request_parameters = {
  #  "method.request.path.proxy" = true
  #}
}

resource "aws_api_gateway_deployment" "deploy" {
  depends_on              = [ "aws_api_gateway_method.proxy_root" ]

  rest_api_id             = "${aws_api_gateway_rest_api.api.id}"
  stage_name              = "${var.environment}"
}

resource "aws_api_gateway_integration" "lambda_root" {
  rest_api_id             = "${aws_api_gateway_rest_api.api.id}"
  resource_id             = "${aws_api_gateway_resource.resource.id}"
  http_method             = "${aws_api_gateway_method.proxy_root.http_method}"

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "${var.lambda_invoke_arn}"
}
resource "aws_api_gateway_integration" "lambda" {
  rest_api_id             = "${aws_api_gateway_rest_api.api.id}"
  resource_id             = "${aws_api_gateway_resource.resource.id}"
  http_method             = "${aws_api_gateway_method.proxy_root.http_method}"

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "${var.lambda_invoke_arn}"
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = "${var.lambda_function_name}"
  principal     = "apigateway.amazonaws.com"

  # The /*/* portion grants access from any method on any resource
  # within the API Gateway "REST API".
  source_arn = "${aws_api_gateway_deployment.deploy.execution_arn}/*/*"
}
/*
resource "aws_api_gateway_base_path_mapping" "mapping" {
  api_id                       = "${aws_api_gateway_rest_api.api.id}"
  stage_name                   = "${aws_api_gateway_deployment.deploy.stage_name}"
  domain_name                  = "${aws_api_gateway_domain_name.domain.domain_name}"
  base_path                    = "${aws_api_gateway_resource.resource.path_part}"
}


resource "aws_api_gateway_domain_name" "domain" {
  domain_name                 = "${var.custom_host_name}.${var.dns_domain}"
  regional_certificate_arn    = "${var.certificate_arn}"
  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

data "aws_route53_zone" "main" {
  name                        = "${var.dns_domain}"
}

resource "aws_route53_record" "record" {
  zone_id                     = "${data.aws_route53_zone.main.id}"
  name                        = "${aws_api_gateway_domain_name.domain.domain_name}"
  type                        = "A"
  alias {
    name                      = "${aws_api_gateway_domain_name.domain.regional_domain_name}"
    zone_id                   = "${aws_api_gateway_domain_name.domain.regional_zone_id}"
    evaluate_target_health    = true
  }
}
*/