# 0005 - Biometrics Model and Threshold

- Status: Accepted
- Date: 2026-10-21

## Context
Facial recognition for attendance. Cameras unknown. Must be tolerant to prescription glasses (non-dark), handle lighting variation, reject dark glasses strictly per requirement. Must run within reasonable time.

## Decision
- Model: Facenet512 (ONNX) via DeepFace
- Detector: retinaface by default, configurable (yolov11n as faster alternative)
- Metric: cosine distance
- Threshold: configurable, start at 0.32 (do NOT use literal 80% -> 0.20)
- Alignment: enabled
- Preprocessing: use DeepFace alignment
- Store only embeddings (vector(512)) in pgvector, never original images
- Load models at startup (lifespan) to avoid cold start
- Run inference in threadpool (CPU-bound)

## Consequences
- Better balance of accuracy/speed for unknown camera quality
- Threshold must be calibrated in real environment
- Dark glasses may still be problematic; need to consider heuristics if strict rejection required
