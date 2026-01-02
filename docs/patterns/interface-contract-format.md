# Interface Contract Format

## Overview

Interface contracts define the agreement between backend and frontend for fullstack sprints. They prevent integration mismatches by validating GraphQL schemas, type definitions, and enum conventions before parallel agent execution.

## When to Use

- **Required**: Fullstack sprints (backend + frontend work)
- **Optional**: Backend-only, frontend-only, integration, or data-layer sprints
- **Phase**: 1.5 (between Planning and Implementation)

## Contract Structure

```json
{
  "sprint": <number>,
  "type": "fullstack",
  "backend_interface": {
    "queries": { ... },
    "mutations": { ... },
    "types": { ... },
    "enums": { ... }
  },
  "frontend_interface": {
    "hooks": [ ... ],
    "types": [ ... ],
    "components": [ ... ]
  },
  "test_interface": {
    "backend_assertions": [ ... ],
    "frontend_assertions": [ ... ]
  }
}
```

## Backend Interface

### Queries

Define GraphQL queries exposed by the backend:

```json
"queries": {
  "userFeatures": "returns: [Feature!]!",
  "featureByKey": "returns: Feature"
}
```

**Format**: `"queryName": "returns: <GraphQL Type>"`

### Mutations

Define GraphQL mutations:

```json
"mutations": {
  "enableFeature": "returns: Feature!",
  "disableFeature": "returns: Boolean!"
}
```

### Types

Define GraphQL object types with field definitions:

```json
"types": {
  "Feature": {
    "key": "String!",
    "name": "String!",
    "enabled": "Boolean!",
    "status": "FeatureStatus!",
    "metadata": {
      "type": "[MetadataField!]",
      "fields": {
        "key": "String!",
        "value": "String!"
      }
    }
  }
}
```

**Nested Types**: Use object notation with `type` and `fields` properties.

**Scalar Types**: `String`, `Int`, `Float`, `Boolean`, `ID`

**Modifiers**:
- `!` = Non-null
- `[Type]` = Array
- `[Type!]!` = Non-null array of non-null elements

### Enums

Define enum types with **UPPERCASE** values:

```json
"enums": {
  "FeatureStatus": ["ENABLED", "DISABLED", "BETA", "DEPRECATED"]
}
```

**CRITICAL**: Enum values MUST be UPPERCASE. This prevents GraphQL enum case mismatches.

## Frontend Interface

### Hooks

React hooks that consume backend data:

```json
"hooks": ["useFeatures", "useHasFeature", "useToggleFeature"]
```

**Naming Convention**: Must start with `use` (React convention)

### Types

TypeScript types/interfaces used by frontend (must match backend types or enums):

```json
"types": ["Feature", "FeatureStatus", "MetadataField"]
```

### Components (Optional)

React components that render data:

```json
"components": ["FeatureList", "FeatureToggle", "FeatureCard"]
```

## Test Interface (Optional)

Define required test assertions for backend and frontend:

```json
"test_interface": {
  "backend_assertions": [
    "Query userFeatures returns array of Feature objects",
    "Mutation enableFeature sets enabled=true",
    "Feature.status enum only accepts UPPERCASE values"
  ],
  "frontend_assertions": [
    "useFeatures hook returns Feature[] matching backend type",
    "FeatureToggle component handles FeatureStatus enum correctly"
  ]
}
```

## GraphQL & Apollo Testing Requirements

### Backend GraphQL Validation

All GraphQL queries and mutations defined in the contract MUST be tested:

```python
# Test each query
def test_user_features_query():
    """Verify userFeatures query matches contract."""
    result = client.execute(gql('''
        query {
            userFeatures {
                key
                name
                enabled
                status
            }
        }
    '''))

    # Verify return type matches contract: [Feature!]!
    assert isinstance(result['userFeatures'], list)
    for feature in result['userFeatures']:
        assert 'key' in feature
        assert 'name' in feature
        assert 'enabled' in feature
        assert feature['status'] in ['ENABLED', 'DISABLED', 'BETA', 'DEPRECATED']
```

### Frontend Apollo Validation

All hooks must be tested against the contract:

```typescript
describe('useFeatures hook', () => {
  it('should match contract interface', async () => {
    const { result } = renderHook(() => useFeatures());

    await waitFor(() => expect(result.current.loading).toBe(false));

    // Verify type matches contract
    const features: Feature[] = result.current.data;
    features.forEach(feature => {
      expect(feature).toHaveProperty('key');
      expect(feature).toHaveProperty('name');
      expect(feature).toHaveProperty('enabled');
      expect(feature.status).toMatch(/^(ENABLED|DISABLED|BETA|DEPRECATED)$/);
    });
  });
});
```

## Validation Rules

1. **Enum Case**: All enum values must be UPPERCASE
2. **Type Matching**: Frontend types must be defined in backend interface
3. **Hook Naming**: Hooks must start with `use` and use camelCase
4. **GraphQL Types**: Query/mutation return types must be defined or scalar
5. **Nested Types**: Nested type references must be defined
6. **Response Shapes**: Full structure validation for nested types

## Example Contract

See `templates/contract-example.json` for a complete example.

## Workflow Integration

1. **Step 1.5.1**: Plan agent or developer creates contract file
   - Location: `.claude/sprint-<N>-contract.json` or `docs/sprints/.../contract-sprint-<N>.json`

2. **Step 1.5.2**: Validation gate runs automatically
   - Command: `python3 scripts/validate_interface_contract.py --sprint <N>`
   - Must pass before proceeding to Phase 2

3. **Phase 2-3**: Implementation and testing
   - Backend: Test all GraphQL queries/mutations against contract
   - Frontend: Test all hooks against contract types
   - Apollo: Verify client queries match contract structure

4. **Pre-flight Checklist**: Verify contract compliance
   - All backend GraphQL endpoints tested
   - All frontend hooks tested
   - Contract validation still passes

## Benefits

- **Prevents Integration Bugs**: Catches type mismatches before implementation
- **Eliminates Enum Case Issues**: Enforces UPPERCASE convention
- **Clear Interface Agreement**: Frontend and backend agree upfront
- **Parallel Work Safe**: Teams can work independently with confidence
- **Test-Driven**: Contract defines test requirements

## Common Pitfalls

1. **Lowercase Enums**: `"enabled"` → Use `"ENABLED"`
2. **Missing Type Definitions**: Reference `UndefinedType` → Define it first
3. **Incorrect Hook Naming**: `getFeatures` → Use `useFeatures`
4. **Skipping Nested Types**: Define all nested structures completely
5. **Not Testing GraphQL Calls**: Must test every query/mutation in contract
6. **Not Testing Apollo Hooks**: Must verify hook data matches contract types
