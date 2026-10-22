# 0006 - Biometric Data Privacy

- Status: Accepted
- Date: 2026-10-21

## Context
Face embeddings are biometric data. Must not store original images. Need to consider privacy, retention, and audit.

## Decision
- Never persist original face images
- Store only numeric embeddings (vector) in DB
- Limit logging (no PII, no embeddings)
- Apply tenant isolation to all biometric data
- Audit access to verification endpoints
- Consider retention/deletion policy per requirements

## Consequences
- Reduced privacy risk
- Smaller storage
- Must be careful with logs and backups
