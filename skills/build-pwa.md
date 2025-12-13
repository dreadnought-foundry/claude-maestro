---
name: "build-pwa"
description: "Build the mobile PWA and check for errors"
---

# Skill: Build PWA

Build the React PWA and verify no build errors.

## When to Use

- After frontend changes
- Before deployment
- As part of quality review
- After dependency updates

## Steps

1. **Check Node Dependencies**
   ```bash
   cd /Volumes/Foundry/Development/CorrData/POC/mobile-pwa
   npm ls --depth=0 2>&1 | head -20
   ```

2. **Run TypeScript Check**
   ```bash
   cd /Volumes/Foundry/Development/CorrData/POC/mobile-pwa
   npx tsc --noEmit 2>&1 | tail -30
   ```

   Expected: No errors

3. **Run ESLint**
   ```bash
   cd /Volumes/Foundry/Development/CorrData/POC/mobile-pwa
   npm run lint 2>&1 | tail -20
   ```

4. **Build Production Bundle**
   ```bash
   cd /Volumes/Foundry/Development/CorrData/POC/mobile-pwa
   npm run build 2>&1
   ```

   Expected: Build succeeds without errors

5. **Check Bundle Size**
   ```bash
   cd /Volumes/Foundry/Development/CorrData/POC/mobile-pwa
   du -sh dist/ 2>/dev/null || echo "dist/ not found"
   ls -la dist/assets/*.js 2>/dev/null | head -5
   ```

6. **Verify Critical Files**
   ```bash
   cd /Volumes/Foundry/Development/CorrData/POC/mobile-pwa
   for f in dist/index.html dist/manifest.json dist/sw.js; do
       if [ -f "$f" ]; then
           echo "✓ $f exists"
       else
           echo "✗ $f MISSING"
       fi
   done
   ```

## Success Criteria

- TypeScript compiles without errors
- ESLint passes
- Build completes successfully
- dist/ folder created with expected files
- Bundle size reasonable (< 5MB for initial load)

## Output Format

```json
{
  "skill": "build-pwa",
  "status": "pass|fail",
  "checks": {
    "typescript": true|false,
    "eslint": true|false,
    "build": true|false,
    "files_present": true|false
  },
  "bundle_size_mb": 0.0,
  "errors": []
}
```

## Common Issues

### TypeScript Errors
- Usually type mismatches after GraphQL schema changes
- Run `npm run codegen` to regenerate types

### Build Fails with Memory Error
- Increase Node memory: `NODE_OPTIONS=--max_old_space_size=4096 npm run build`

### Missing Peer Dependencies
- Run `npm install` to update dependencies
