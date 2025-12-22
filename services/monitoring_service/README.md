# Monitoring service

Collects prediction/outcome pairs, computes simple aggregates (counts, drift proxy), and logs/returns the results so observability hooks exist even in the symbolic pipeline.

## Lambda contract

- Input:  
  `predictions` – list of dictionaries emitted by the inference Lambda.  
  `actuals` – optional list of ground-truth labels (string or numeric).  
  `dataset_tag` – identifier for CloudWatch logs (defaults to `demo`).
- Output: JSON with accuracy/drift style counters, always safe to call without actual labels.

## Packaging

```
cd services/monitoring_service
task build
```

Produces `dist/monitoring-lambda.zip`.
