# Inference service

Loads the latest model artifact, applies a symbolic scoring rule to incoming feature rows, and returns lightweight prediction metadata. The goal is to show how the serving side of the pipeline can stay just as small as the training/model Lambda.

## Lambda contract

- Input (keys are optional):  
  `artifact_bucket`, `artifact_key` – where the model service stored its JSON summary.  
  `inputs` – list of feature dictionaries (defaults to an empty list).  
  `decision_boundary` – override for the heuristic threshold derived from the artifact.
- Output: prediction list plus model metadata (version + bucket/key).

Environment defaults: `INFERENCE_ARTIFACT_BUCKET`, `INFERENCE_ARTIFACT_KEY`.

## Packaging

```
cd services/inference_service
task build
```

Generates `dist/inference-lambda.zip`.
