"""Validate the CloudFormation template structure without deploying to AWS."""
from __future__ import annotations

import pathlib
from typing import Any, Dict, List, Set, cast

import pytest
import yaml  # type: ignore[import-untyped]

TEMPLATE_PATH = pathlib.Path(__file__).parents[2] / "template.yaml"

# CloudFormation intrinsic-function tags that yaml.safe_load rejects.
# Register them as plain scalars so the loader doesn't error.
_CF_TAGS = [
    "!Sub", "!Ref", "!GetAtt", "!If", "!Select", "!Split",
    "!Join", "!And", "!Or", "!Not", "!Equals", "!Condition",
    "!ImportValue", "!FindInMap", "!Base64", "!Cidr",
]


def _build_loader() -> Any:  # returns a yaml.Loader subclass
    class CfnLoader(yaml.SafeLoader):  # type: ignore[misc]
        pass

    def _scalar(loader: Any, tag: Any, node: Any) -> Any:
        return loader.construct_scalar(node)

    for tag in _CF_TAGS:
        CfnLoader.add_multi_constructor(tag, _scalar)

    return CfnLoader

REQUIRED_RESOURCE_TYPES = {
    "AWS::S3::Bucket",
    "AWS::CloudFront::Distribution",
    "AWS::Lambda::Function",
    "AWS::Lambda::LayerVersion",
    "AWS::ApiGatewayV2::Api",
    "AWS::IAM::Role",
    "AWS::SecretsManager::Secret",
    "AWS::Logs::LogGroup",
}


@pytest.fixture(scope="module")
def template() -> Dict[str, Any]:
    loader = _build_loader()
    return cast(Dict[str, Any], yaml.load(TEMPLATE_PATH.read_text(), Loader=loader))


@pytest.fixture(scope="module")
def resources(template: Dict[str, Any]) -> Dict[str, Any]:
    return cast(Dict[str, Any], template["Resources"])


def resource_types(resources: Dict[str, Any]) -> Set[str]:
    return {r["Type"] for r in resources.values()}


def resources_of_type(resources: Dict[str, Any], rtype: str) -> List[Dict[str, Any]]:
    return [r for r in resources.values() if r["Type"] == rtype]


def _as_action_list(action: Any) -> List[str]:
    """Normalise a CloudFormation Action value to a list of strings."""
    return [action] if isinstance(action, str) else list(action)


# ── Slice 1: required resource types ────────────────────────────────────────


def test_template_has_all_required_resource_types(
    resources: Dict[str, Any],
) -> None:
    present = resource_types(resources)
    missing = REQUIRED_RESOURCE_TYPES - present
    assert not missing, f"Missing resource types: {missing}"


def test_template_has_two_s3_buckets(resources: Dict[str, Any]) -> None:
    buckets = resources_of_type(resources, "AWS::S3::Bucket")
    assert len(buckets) >= 2, "Expected at least 2 S3 buckets (frontend + context)"


# ── Slice 2: Lambda configuration ────────────────────────────────────────────


def test_lambda_memory_is_256mb(resources: Dict[str, Any]) -> None:
    functions = resources_of_type(resources, "AWS::Lambda::Function")
    assert functions, "No Lambda functions found"
    fn = functions[0]["Properties"]
    assert fn["MemorySize"] == 256, f"Expected 256MB, got {fn['MemorySize']}"


def test_lambda_handler_is_mangum_entrypoint(resources: Dict[str, Any]) -> None:
    functions = resources_of_type(resources, "AWS::Lambda::Function")
    fn = functions[0]["Properties"]
    assert fn["Handler"] == "app.main.handler", (
        f"Expected app.main.handler, got {fn['Handler']}"
    )


def test_lambda_runtime_is_python313(resources: Dict[str, Any]) -> None:
    functions = resources_of_type(resources, "AWS::Lambda::Function")
    fn = functions[0]["Properties"]
    assert fn["Runtime"] == "python3.13"


def test_lambda_architecture_is_arm64(resources: Dict[str, Any]) -> None:
    # Architecture must be explicit and match the layer. Without this, Lambda
    # defaults to x86_64 but the layer could silently mismatch, causing
    # ImportModuleError for compiled extensions like pydantic_core. arm64 is
    # used because Docker on M-series Macs builds arm64 binaries natively.
    functions = resources_of_type(resources, "AWS::Lambda::Function")
    fn = functions[0]["Properties"]
    assert fn.get("Architectures") == ["arm64"]


def test_layer_compatible_architecture_is_arm64(resources: Dict[str, Any]) -> None:
    layers = resources_of_type(resources, "AWS::Lambda::LayerVersion")
    assert layers, "No Lambda layer found"
    layer = layers[0]["Properties"]
    assert layer.get("CompatibleArchitectures") == ["arm64"]


# ── Slice 3: CloudWatch Log Group ─────────────────────────────────────────────


def test_log_group_retention_is_30_days(resources: Dict[str, Any]) -> None:
    log_groups = resources_of_type(resources, "AWS::Logs::LogGroup")
    assert log_groups, "No CloudWatch Log Groups found"
    lg = log_groups[0]["Properties"]
    assert lg["RetentionInDays"] == 30, (
        f"Expected 30-day retention, got {lg['RetentionInDays']}"
    )


# ── Slice 4: API Gateway HTTP API v2 ──────────────────────────────────────────


def test_api_gateway_is_http_protocol(resources: Dict[str, Any]) -> None:
    apis = resources_of_type(resources, "AWS::ApiGatewayV2::Api")
    assert apis, "No ApiGatewayV2::Api found"
    api = apis[0]["Properties"]
    assert api["ProtocolType"] == "HTTP", (
        f"Expected HTTP protocol (v2), got {api['ProtocolType']}"
    )


def test_api_gateway_has_default_stage_with_autodeploy(resources: Dict[str, Any]) -> None:
    stages = resources_of_type(resources, "AWS::ApiGatewayV2::Stage")
    assert stages, "No ApiGatewayV2::Stage found"
    stage = stages[0]["Properties"]
    assert stage["AutoDeploy"] is True


def test_api_gateway_has_no_cors_configuration(resources: Dict[str, Any]) -> None:
    # CorsConfiguration on the Api would reference Distribution.DomainName,
    # creating a circular dependency. CORS is handled by CloudFront instead.
    apis = resources_of_type(resources, "AWS::ApiGatewayV2::Api")
    api = apis[0]["Properties"]
    assert "CorsConfiguration" not in api, (
        "Api must not have CorsConfiguration — it creates a circular dependency "
        "with Distribution. Handle CORS at the CloudFront layer instead."
    )


def test_lambda_allowed_origins_does_not_reference_distribution(
    resources: Dict[str, Any],
) -> None:
    # ALLOWED_ORIGINS must not use !Sub against Distribution.DomainName —
    # that creates a circular dependency. It must be a plain parameter reference.
    functions = resources_of_type(resources, "AWS::Lambda::Function")
    env_vars = functions[0]["Properties"]["Environment"]["Variables"]
    allowed = env_vars.get("ALLOWED_ORIGINS", "")
    assert "Distribution" not in str(allowed), (
        "ALLOWED_ORIGINS must not reference Distribution — use the AllowedOrigins "
        "parameter instead and update the value post-deploy."
    )


# ── Slice 5: IAM role permissions ─────────────────────────────────────────────


def _iam_policy_statements(resources: Dict[str, Any]) -> List[Dict[str, Any]]:
    roles = resources_of_type(resources, "AWS::IAM::Role")
    assert roles, "No IAM roles found"
    stmts: List[Dict[str, Any]] = []
    for policy in roles[0]["Properties"].get("Policies", []):
        stmts.extend(policy["PolicyDocument"]["Statement"])
    return stmts


def test_iam_role_allows_bedrock_invoke_model(resources: Dict[str, Any]) -> None:
    stmts = _iam_policy_statements(resources)
    matches = [s for s in stmts if "bedrock:InvokeModel" in _as_action_list(s["Action"])]
    assert matches, "No IAM statement grants bedrock:InvokeModel"


def test_iam_role_allows_s3_context_access(resources: Dict[str, Any]) -> None:
    required = {"s3:GetObject", "s3:PutObject", "s3:DeleteObject"}
    covered: Set[str] = set()
    for stmt in _iam_policy_statements(resources):
        covered |= required & set(_as_action_list(stmt["Action"]))
    assert covered == required, f"Missing S3 actions: {required - covered}"


def test_iam_role_allows_secrets_manager_read(resources: Dict[str, Any]) -> None:
    stmts = _iam_policy_statements(resources)
    matches = [
        s for s in stmts
        if "secretsmanager:GetSecretValue" in _as_action_list(s["Action"])
    ]
    assert matches, "No IAM statement grants secretsmanager:GetSecretValue"
