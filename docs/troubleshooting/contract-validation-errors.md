# Contract Validation Error Troubleshooting

This guide helps you fix common interface contract validation errors.

## Error Categories

1. [Enum Case Errors](#enum-case-errors)
2. [Type Mismatch Errors](#type-mismatch-errors)
3. [Undefined Type Errors](#undefined-type-errors)
4. [Hook Naming Errors](#hook-naming-errors)
5. [Query/Mutation Format Errors](#querymutation-format-errors)
6. [Schema Validation Errors](#schema-validation-errors)
7. [GraphQL Testing Errors](#graphql-testing-errors)
8. [Apollo Testing Errors](#apollo-testing-errors)

---

## Enum Case Errors

### Error Message
```
Enum value 'enabled' in enum 'FeatureStatus' must be UPPERCASE. Use 'ENABLED' instead.
```

### Cause
GraphQL enum values must be UPPERCASE to prevent case-sensitivity issues.

### Fix
Change all enum values to UPPERCASE:

**Before:**
```json
"enums": {
  "FeatureStatus": ["enabled", "disabled", "Beta"]
}
```

**After:**
```json
"enums": {
  "FeatureStatus": ["ENABLED", "DISABLED", "BETA"]
}
```

### Prevention
- Always use UPPERCASE for enum values
- Use underscores for multi-word enums: `"IN_PROGRESS"`, `"NOT_STARTED"`

---

## Type Mismatch Errors

### Error Message
```
Frontend type 'UserProfile' not defined in backend interface.
Available backend types: ['User', 'Feature', 'FeatureStatus']
```

### Cause
Frontend references a type that doesn't exist in the backend interface.

### Fix
Either:
1. **Add the type to backend** if it should exist:
   ```json
   "backend_interface": {
     "types": {
       "UserProfile": {
         "userId": "ID!",
         "displayName": "String!"
       }
     }
   }
   ```

2. **Remove from frontend** if it was a mistake:
   ```json
   "frontend_interface": {
     "types": ["User", "Feature"]  // Removed 'UserProfile'
   }
   ```

### Prevention
- Define backend types first
- Share contract with frontend team before implementation
- Use contract-example.json as template

---

## Undefined Type Errors

### Error Message
```
Field 'getFeature' references undefined type 'Feature'. Define it in backend_interface.types or backend_interface.enums
```

### Cause
Query/mutation return type is not defined in backend interface.

### Fix
Add the type definition:

```json
"backend_interface": {
  "queries": {
    "getFeature": "returns: Feature!"
  },
  "types": {
    "Feature": {
      "key": "String!",
      "name": "String!",
      "enabled": "Boolean!"
    }
  }
}
```

### Nested Type Example
If using nested types:

```json
"types": {
  "Feature": {
    "metadata": {
      "type": "[MetadataField!]",
      "fields": {
        "key": "String!",
        "value": "String!"
      }
    }
  },
  "MetadataField": {  // Must define nested type separately too
    "key": "String!",
    "value": "String!"
  }
}
```

---

## Hook Naming Errors

### Error Message
```
Hook 'getFeatures' must start with 'use' (React convention). Rename to 'useGetFeatures'
```

### Cause
React hooks must follow `useXxx` naming convention.

### Fix
**Before:**
```json
"frontend_interface": {
  "hooks": ["getFeatures", "fetchData", "loadUser"]
}
```

**After:**
```json
"frontend_interface": {
  "hooks": ["useFeatures", "useData", "useUser"]
}
```

### Prevention
- All hooks start with `use`
- Use camelCase: `useFeatureData`, not `use_feature_data`

---

## Query/Mutation Format Errors

### Error Message
```
Query 'userFeatures' return specification must start with 'returns:'. Got: '[Feature!]!'
```

### Cause
Missing `returns:` prefix in query/mutation specification.

### Fix
**Before:**
```json
"queries": {
  "userFeatures": "[Feature!]!"
}
```

**After:**
```json
"queries": {
  "userFeatures": "returns: [Feature!]!"
}
```

### Valid Formats
```json
"queries": {
  "getUser": "returns: User",
  "getUsers": "returns: [User!]!",
  "hasFeature": "returns: Boolean!",
  "getMetadata": "returns: [MetadataField!]"
}
```

---

## Schema Validation Errors

### Error Message
```
Schema validation failed: 'backend_interface' is a required property
```

### Cause
Missing required top-level fields in contract.

### Fix
Ensure contract has all required fields:

```json
{
  "sprint": 3,                  // Required
  "type": "fullstack",          // Required
  "backend_interface": { ... }, // Required
  "frontend_interface": { ... } // Required
}
```

### Required Nested Fields
- `backend_interface` can be empty `{}` but must exist
- `frontend_interface` can be empty `{}` but must exist
- `test_interface` is optional

---

## GraphQL Testing Errors

### Error Message
```
Backend GraphQL call 'userFeatures' not tested against contract
```

### Cause
Contract requires testing all GraphQL queries/mutations, but test is missing.

### Fix
Add backend test for each query/mutation in contract:

```python
# tests/test_sprint_3_backend.py

def test_user_features_query_matches_contract(graphql_client):
    """Verify userFeatures query returns [Feature!]! per contract."""
    query = gql('''
        query {
            userFeatures {
                key
                name
                enabled
                status
            }
        }
    '''))

    result = graphql_client.execute(query)

    # Verify contract compliance
    assert isinstance(result['userFeatures'], list)
    assert len(result['userFeatures']) >= 0

    for feature in result['userFeatures']:
        # Verify Feature type structure
        assert 'key' in feature
        assert 'name' in feature
        assert 'enabled' in feature
        assert isinstance(feature['enabled'], bool)

        # Verify enum values are UPPERCASE
        assert feature['status'] in ['ENABLED', 'DISABLED', 'BETA', 'DEPRECATED']


def test_enable_feature_mutation_matches_contract(graphql_client):
    """Verify enableFeature mutation returns Feature! per contract."""
    mutation = gql('''
        mutation($key: String!) {
            enableFeature(key: $key) {
                key
                name
                enabled
                status
            }
        }
    '''))

    result = graphql_client.execute(mutation, variable_values={"key": "test-feature"})

    feature = result['enableFeature']
    assert feature is not None
    assert feature['enabled'] is True
```

### Prevention
- Test every query and mutation in contract
- Verify return types match contract specifications
- Check enum values are UPPERCASE
- Test nested type structures

---

## Apollo Testing Errors

### Error Message
```
Frontend Apollo hook 'useFeatures' not tested against contract types
```

### Cause
Contract requires testing all frontend hooks, but test is missing.

### Fix
Add frontend test for each hook in contract:

```typescript
// tests/useFeatures.test.ts

import { renderHook, waitFor } from '@testing-library/react';
import { MockedProvider } from '@apollo/client/testing';
import { useFeatures } from './useFeatures';
import { Feature, FeatureStatus } from './types';

describe('useFeatures hook - Contract Validation', () => {
  it('should return data matching Feature type from contract', async () => {
    const { result } = renderHook(() => useFeatures(), {
      wrapper: ({ children }) => (
        <MockedProvider mocks={[/* mock data */]}>
          {children}
        </MockedProvider>
      ),
    });

    await waitFor(() => expect(result.current.loading).toBe(false));

    const features: Feature[] = result.current.data;

    // Verify array type
    expect(Array.isArray(features)).toBe(true);

    // Verify each feature matches contract
    features.forEach((feature: Feature) => {
      // Required fields from contract
      expect(feature).toHaveProperty('key');
      expect(feature).toHaveProperty('name');
      expect(feature).toHaveProperty('enabled');
      expect(feature).toHaveProperty('status');

      // Type checks
      expect(typeof feature.key).toBe('string');
      expect(typeof feature.name).toBe('string');
      expect(typeof feature.enabled).toBe('boolean');

      // Enum validation (UPPERCASE values)
      expect(feature.status).toMatch(/^(ENABLED|DISABLED|BETA|DEPRECATED)$/);
    });
  });

  it('should handle nested metadata fields per contract', async () => {
    const { result } = renderHook(() => useFeatures(), {
      wrapper: MockedProvider,
    });

    await waitFor(() => expect(result.current.loading).toBe(false));

    const featureWithMetadata = result.current.data[0];

    if (featureWithMetadata.metadata) {
      expect(Array.isArray(featureWithMetadata.metadata)).toBe(true);

      featureWithMetadata.metadata.forEach((field) => {
        expect(field).toHaveProperty('key');
        expect(field).toHaveProperty('value');
        expect(typeof field.key).toBe('string');
        expect(typeof field.value).toBe('string');
      });
    }
  });
});
```

### Prevention
- Test every hook in contract
- Verify hook return types match backend types
- Test enum value formats (UPPERCASE)
- Test nested type structures
- Use TypeScript for type safety

---

## Performance Issues

### Error Message
```
Validation took 6.2s, should be < 5s
```

### Cause
Contract is too large or validation logic is inefficient.

### Fix
1. **Reduce contract size** if possible (split into multiple contracts)
2. **Check for validation loops** in nested types
3. **Profile validation** to find slow sections

### Prevention
- Keep contracts focused on single feature area
- Limit nesting depth to 3-4 levels
- Run performance test: `pytest tests/test_interface_contract_validation.py::test_validation_performance`

---

## Common Workflow Issues

### Issue: "Contract validation blocks my sprint!"

**Solution:**
1. Fix validation errors (see above)
2. Contract validation is **mandatory** for fullstack sprints - this prevents costly integration bugs
3. For backend-only or frontend-only sprints, validation is skipped

### Issue: "Plan agent didn't generate contract"

**Solution:**
1. Manually create contract file: `.claude/sprint-<N>-contract.json`
2. Use `templates/contract-example.json` as template
3. Run validation: `python3 scripts/validate_interface_contract.py --sprint <N>`

### Issue: "Contract passes validation but tests still fail"

**Solution:**
Contract validation only checks structure, not runtime behavior:
1. Verify GraphQL backend tests match contract (see [GraphQL Testing](#graphql-testing-errors))
2. Verify Apollo frontend tests match contract (see [Apollo Testing](#apollo-testing-errors))
3. Check for type conversion issues (String vs Int)
4. Verify enum values in actual code match contract

---

## Getting Help

1. **Check contract-example.json** for valid format
2. **Read docs/patterns/interface-contract-format.md** for full specification
3. **Run validation with verbose output**: `python3 scripts/validate_interface_contract.py <contract-file> -v`
4. **Test incrementally**: Start with minimal contract, add complexity gradually

## Quick Checklist

Before submitting contract for validation:

- [ ] All enum values are UPPERCASE
- [ ] All types referenced are defined
- [ ] Hooks start with `use`
- [ ] Queries/mutations have `returns:` prefix
- [ ] Required fields present: `sprint`, `type`, `backend_interface`, `frontend_interface`
- [ ] Nested types fully defined
- [ ] Backend GraphQL tests written for all queries/mutations
- [ ] Frontend Apollo tests written for all hooks
- [ ] Tests verify enum UPPERCASE values
- [ ] Tests verify nested type structures
