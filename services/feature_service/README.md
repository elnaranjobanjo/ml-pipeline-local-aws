# Feature service

Consumes the CSV dropped by the data ingest Lambda, derives a couple of engineered values (price change, normalized volume), and publishes a JSON-lines feature set for the model service.

## Lambda contract

- Input (optional keys):  
  `source_bucket`, `source_key` – location of the raw CSV.  
  `feature_bucket`, `feature_key` – where to write the JSON output.  
  Keys accept `${uuid}` placeholders so multiple runs can coexist.
- Output: JSON summary with counts and small previews of the generated feature rows.

Environment variables provide the same options (`FEATURE_SOURCE_BUCKET`, `FEATURE_SOURCE_KEY`, `FEATURE_BUCKET`, `FEATURE_KEY`).

## Packaging

```
cd services/feature_service
task build
```

Packages the Lambda as `dist/feature-lambda.zip`.
