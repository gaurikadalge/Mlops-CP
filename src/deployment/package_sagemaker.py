"""
Packaging utility for AWS SageMaker deployment.
Bundles model artifacts and inference handlers into a deployable model.tar.gz archive
and performs local offline verification.
"""
import os
import sys
import glob
import shutil
import tarfile
import json
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.deployment.inference import model_fn, input_fn, predict_fn, output_fn


def find_latest_model_artifact() -> str:
    """Finds the most recent model.ubj artifact in mlruns or adaptive-ids/mlruns."""
    patterns = [
        os.path.join(PROJECT_ROOT, "adaptive-ids/mlruns/1/models/*/artifacts/model.ubj"),
        os.path.join(PROJECT_ROOT, "mlruns/1/models/*/artifacts/model.ubj"),
        os.path.join(PROJECT_ROOT, "mlruns/*/artifacts/model.ubj"),
    ]
    candidates = []
    for pat in patterns:
        candidates.extend(glob.glob(pat))
        
    if not candidates:
        raise FileNotFoundError("No trained model.ubj found in mlruns directories.")
        
    candidates.sort(key=os.path.getmtime, reverse=True)
    return candidates[0]


def package_model(output_dir: str = "build/sagemaker") -> str:
    """
    Creates model.tar.gz containing model artifact and code/ directory.
    """
    os.makedirs(output_dir, exist_ok=True)
    staging_dir = os.path.join(output_dir, "staging")
    if os.path.exists(staging_dir):
        shutil.rmtree(staging_dir)
    os.makedirs(staging_dir, exist_ok=True)
    
    # 1. Copy model artifact
    model_src = find_latest_model_artifact()
    model_dest = os.path.join(staging_dir, "model.ubj")
    shutil.copy2(model_src, model_dest)
    print(f"Bundled model artifact from: {model_src}")
    
    # 2. Copy inference code
    code_dir = os.path.join(staging_dir, "code")
    os.makedirs(code_dir, exist_ok=True)
    inf_src = os.path.join(PROJECT_ROOT, "src/deployment/inference.py")
    shutil.copy2(inf_src, os.path.join(code_dir, "inference.py"))
    
    # 3. Add requirements.txt for container
    with open(os.path.join(code_dir, "requirements.txt"), "w") as f:
        f.write("xgboost>=2.0.0\npandas>=2.0.0\nnumpy>=1.24.0\n")
        
    # 4. Copy preprocessing metadata if available
    meta_src = os.path.join(PROJECT_ROOT, "outputs/preprocessing_metadata.json")
    if os.path.exists(meta_src):
        shutil.copy2(meta_src, os.path.join(staging_dir, "preprocessing_metadata.json"))

        
    # 4. Create tar.gz
    tar_path = os.path.join(output_dir, "model.tar.gz")
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(staging_dir, arcname=".")
        
    print(f"Successfully created SageMaker archive at: {tar_path}")
    return tar_path


def test_local_inference(tar_path: str):
    """
    Tests model_fn, input_fn, predict_fn, and output_fn locally against the packaged archive.
    """
    import tempfile
    print("\n--- Verifying SageMaker Local Inference ---")
    with tempfile.TemporaryDirectory() as tmp_dir:
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=tmp_dir)
            
        # 1. model_fn
        loaded_model = model_fn(tmp_dir)
        print("✓ model_fn loaded model successfully.")
        
        # 2. input_fn (JSON)
        sample_json = json.dumps({
            "features": {
                "Flow Duration": 120.0,
                "Flow Bytes/s": 4500.0,
                "Packet Length Mean": 55.0
            }
        })
        input_df = input_fn(sample_json, "application/json")
        print(f"✓ input_fn processed JSON input ({input_df.shape[0]} row, {input_df.shape[1]} cols).")
        
        # 3. predict_fn
        preds = predict_fn(input_df, loaded_model)
        assert len(preds) == 1
        print(f"✓ predict_fn result: {preds[0]}")
        
        # 4. output_fn
        out_body, out_content_type = output_fn(preds, "application/json")
        assert out_content_type == "application/json"
        parsed = json.loads(out_body)
        assert "predictions" in parsed
        print(f"✓ output_fn serialized response: {out_body}")
        
    print("--- All SageMaker Local Inference Checks PASSED! ---")


if __name__ == "__main__":
    tar_file = package_model()
    test_local_inference(tar_file)
