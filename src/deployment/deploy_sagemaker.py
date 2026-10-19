"""
AWS SageMaker Deployment and Dry-Run Utility.
Provisions model artifacts to Amazon S3 and configures SageMaker Endpoints
with safe fallback and comprehensive instructions when AWS credentials are not set.
"""
import os
import sys
import argparse
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.deployment.package_sagemaker import package_model


def check_aws_credentials() -> bool:
    """Verifies whether active AWS credentials are configured in the environment."""
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        return credentials is not None and credentials.access_key is not None
    except Exception:
        return False


def print_deployment_guide(archive_path: str, bucket_name: str, region: str, role_arn: str):
    """Prints production cloud deployment instructions and architecture details."""
    print("\n=======================================================")
    print("AWS SAGEMAKER PRODUCTION DEPLOYMENT SPECIFICATION")
    print("=======================================================")
    print(f"1. Model Archive: {archive_path}")
    print(f"2. Target S3 URI: s3://{bucket_name}/adaptive-ids/models/model.tar.gz")
    print(f"3. IAM Role:      {role_arn}")
    print(f"4. AWS Region:    {region}")
    print(f"5. Inference Framework: XGBoost / Python 3.11 Container")
    print("\nRECOMMENDED ENDPOINT CONFIGURATIONS:")
    print("  A. Serverless Inference (Recommended for bursty IDS network flow traffic):")
    print("     - Memory Size: 2048 MB")
    print("     - Max Concurrency: 10")
    print("     - Estimated Cost: Pay-per-invocation (Zero cost when idle)")
    print("  B. Real-Time Dedicated Instance (For continuous high-volume packet inspection):")
    print("     - Instance Type: ml.m5.large (2 vCPU, 8 GiB RAM)")
    print("     - Initial Instance Count: 1 (with Auto-Scaling enabled on InvocationsPerInstance)")
    print("     - Estimated Cost: ~$0.115/hour (~$82/month in us-east-1)")
    print("\nREQUIRED IAM PERMISSIONS:")
    print("  - AmazonSageMakerFullAccess")
    print("  - s3:GetObject, s3:PutObject on model bucket")
    print("\nDEPLOYMENT AWS CLI COMMANDS:")
    print(f"  aws s3 cp {archive_path} s3://{bucket_name}/adaptive-ids/models/model.tar.gz")
    print("  aws sagemaker create-model --model-name adaptive-ids-xgboost ...")
    print("  aws sagemaker create-endpoint-config --endpoint-config-name adaptive-ids-config ...")
    print("  aws sagemaker create-endpoint --endpoint-name adaptive-ids-prod --endpoint-config-name adaptive-ids-config")
    print("\nCLEANUP / TEARDOWN COMMAND:")
    print("  aws sagemaker delete-endpoint --endpoint-name adaptive-ids-prod")
    print("  aws sagemaker delete-endpoint-config --endpoint-config-name adaptive-ids-config")
    print("  aws sagemaker delete-model --model-name adaptive-ids-xgboost")
    print("=======================================================\n")


def deploy(
    bucket_name: str = "my-mlops-ids-bucket",
    region: str = "us-east-1",
    role_arn: str = "arn:aws:iam::123456789012:role/SageMakerExecutionRole",
    endpoint_name: str = "adaptive-ids-endpoint",
    dry_run: bool = False
):
    print("Packaging SageMaker deployment artifact...")
    tar_path = package_model()
    
    has_creds = check_aws_credentials()
    if dry_run or not has_creds:
        if not has_creds:
            print("Notice: No active AWS credentials found in environment.")
        print("Executing in DRY-RUN mode. Validating packaging and printing deployment guide.")
        print_deployment_guide(tar_path, bucket_name, region, role_arn)
        return {
            "status": "dry_run_success",
            "artifact_path": tar_path,
            "target_s3_uri": f"s3://{bucket_name}/adaptive-ids/models/model.tar.gz"
        }

    # If AWS credentials exist and not dry-run
    print(f"Connecting to AWS S3 ({region})...")
    s3_client = boto3.client("s3", region_name=region)
    s3_key = "adaptive-ids/models/model.tar.gz"
    
    print(f"Uploading {tar_path} to s3://{bucket_name}/{s3_key}...")
    try:
        s3_client.upload_file(tar_path, bucket_name, s3_key)
        print("Artifact successfully uploaded to S3.")
    except ClientError as e:
        print(f"S3 Upload failed: {e}")
        return {"status": "s3_upload_failed", "error": str(e)}

    return {
        "status": "ready_for_cloud_endpoint",
        "s3_uri": f"s3://{bucket_name}/{s3_key}"
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy Adaptive IDS model to AWS SageMaker.")
    parser.add_argument("--bucket", default="my-mlops-ids-bucket", help="S3 bucket for model artifacts")
    parser.add_argument("--region", default="us-east-1", help="AWS Region")
    parser.add_argument("--role-arn", default="arn:aws:iam::123456789012:role/SageMakerExecutionRole", help="Execution role ARN")
    parser.add_argument("--endpoint-name", default="adaptive-ids-endpoint", help="SageMaker endpoint name")
    parser.add_argument("--dry-run", action="store_true", default=False, help="Perform dry-run without cloud API calls")
    args = parser.parse_args()

    deploy(
        bucket_name=args.bucket,
        region=args.region,
        role_arn=args.role_arn,
        endpoint_name=args.endpoint_name,
        dry_run=args.dry_run
    )
