# Vocabulary: Spanish -> English

All code (classes, methods, fields, variables, packages, enums, tables, columns, comments, Javadoc) must be in English. Translate following AML/FATF terminology used in this project.

| Spanish | English | Notes |
| --- | --- | --- |
| Cliente | `Customer` | Subject obliged. Use `customer`, not `client`. |
| Persona física | `NaturalPerson` | FATF term |
| Persona moral | `LegalPerson` | FATF term |
| Número de cliente / folio interno | `customerNumber` | |
| Expediente | `customerFile` / `CustomerDto` | KYC terminology |
| Actividad económica | `economicActivity` | |
| Origen de los recursos | `sourceOfFunds` | FATF term. Do not use `resourceOrigin` |
| PEP | `pep` | Politically Exposed Person. Keep acronym |
| Producto a operar | `product` | |
| Monto estimado de transacciones | `expectedVolume` | AML terminology |
| Instrumento monetario | `monetaryInstrument` | FinCEN term |
| Domicilio | `Address` | |
| Colonia | `neighborhood` | |
| Delegación / municipio | `municipality` | |
| Entidad federativa | `state` | |
| Razón social | `legalName` | |
| Fecha de constitución | `incorporationDate` | |
| Fecha de alta | `onboardingDate` | KYC: onboarding |
| Nivel de riesgo | `riskRating` | Not `riskLevel` |
| Umbral | `threshold` | |
| Beneficiario controlador | `beneficialOwner` | FATF term |

Exceptions (do NOT translate):
1. Country/standard acronyms: `rfc`, `curp`, `pep`, `sat69b`
2. User-facing error messages (Spanish) - concentrated in error handlers
3. Documentation and ADRs
