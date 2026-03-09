# Upgrade Plan: GPT-5.4 (2026-03-05)

## Overview
Upgrade the application from `gpt-5.1` to `gpt-5.4-2026-03-05` with `reasoning_effort: "none"`.

## Current State
- **Model:** `gpt-5.1`
- **Reasoning level:** `"none"` (already configured)
- **Configuration location:** `app/src/app_config.py`
- **Affected pipelines:**
  - Generate Referrals RAG
  - Generate Action Plan
  - OpenAI Web Search (default)

## GPT-5.4 Key Features (from Context7 MCP)
Based on OpenAI API documentation:

### Reasoning Parameter Support
- GPT-5.4 follows the GPT-5.1+ pattern for reasoning support
- **Supported values:** `"none"`, `"minimal"`, `"low"`, `"medium"`, `"high"`, `"xhigh"`
- **Default:** Models after GPT-5.1 continue to support `"none"` reasoning
- **Our choice:** Keep `reasoning_effort: "none"` (no reasoning overhead)

### API Compatibility
- Uses same Responses API format as GPT-5.1/5.2
- Supports tool calls (including web_search) with all reasoning levels
- Same parameter structure: `reasoning: {"effort": "none"}`

## Changes Required

### 1. Update Model Version in Config
**File:** `app/src/app_config.py`

Update three configuration variables:
```python
# Line 71: Default model for all pipelines
default_openai_model_version: str = "gpt-5.4-2026-03-05"

# Line 74: Generate referrals pipeline
generate_referrals_rag_model_version: str = "gpt-5.4-2026-03-05"

# Line 78: Generate action plan pipeline
generate_action_plan_model_version: str = "gpt-5.4-2026-03-05"
```

**Keep existing reasoning levels unchanged:**
- `default_openai_reasoning_level: str = "none"` (line 72)
- `generate_referrals_rag_reasoning_level: str = "none"` (line 75)
- `generate_action_plan_reasoning_level: str = "none"` (line 79)

### 2. Update Prompt JSON Files (Optional)
These files reference older models in metadata but don't affect runtime behavior:

**Files to review:**
- `app/prompts/generate_action_plan.json` (currently `gpt-4o`)
- `app/prompts/generate_referrals_centraltx.json` (currently `gpt-4.1`)
- `app/prompts/generate_referrals_keystone.json` (currently `gpt-4o`)

**Decision:** Update these to `gpt-5.4-2026-03-05` for consistency, but the actual model used is controlled by `app_config.py`.

### 3. Update Sample Pipeline (Optional)
**File:** `app/src/pipelines/sample_pipeline/pipeline_wrapper.py`

Currently hardcodes `gpt-4o-mini` on line 25. Consider updating to use config:
```python
llm = OpenAIChatGenerator(model=config.default_openai_model_version)
```

Or if keeping lightweight for samples, update to a newer mini model.

### 4. No Changes Needed
These components already use config variables correctly:
- ✅ `OpenAIWebSearchGenerator` (uses `config.default_openai_model_version`)
- ✅ All pipeline wrappers (use config for model selection)
- ✅ Reasoning parameter handling (already supports "none")

## Testing Plan

### 1. Verify Configuration
```bash
cd app
grep -r "gpt-5.4" src/app_config.py
# Should show three occurrences
```

### 2. Restart Application
```bash
cd app
docker compose down
docker compose up -d
docker compose logs -f app
```

### 3. Test Generate Referrals Pipeline
**Frontend:** http://localhost:3001/generate-referrals
- Submit a referrals request
- Verify response is generated
- Check Phoenix traces for model version

### 4. Test Generate Action Plan Pipeline
**Frontend:** http://localhost:3001/generate-action-plan (if applicable)
- Submit an action plan request
- Verify response format
- Check Phoenix traces

### 5. Verify Model in Phoenix UI
**Phoenix:** http://localhost:6006
- Navigate to recent traces
- Check span attributes for:
  - `model: "gpt-5.4-2026-03-05"`
  - `reasoning_effort: "none"`
- Verify web_search tool calls still work

### 6. Run Backend Tests
```bash
cd app
make test-coverage
```

### 7. Check Logs for Model Version
```bash
docker compose logs app | grep -i "model="
# Should show gpt-5.4-2026-03-05 in API calls
```

### 8. Frontend Tests
```bash
cd frontend
npm run ts:check && npm run lint && npm run test
```

## Rollback Plan
If issues arise, revert `app/src/app_config.py`:

```bash
git checkout main -- app/src/app_config.py
cd app
docker compose restart app
```

## Performance Considerations

### Expected Changes
- **Latency:** GPT-5.4 may have different latency characteristics than 5.1
- **Cost:** Check OpenAI pricing for GPT-5.4 vs 5.1
- **Quality:** Newer model may produce improved outputs
- **Token usage:** Monitor for changes in token consumption

### Monitoring
After deployment, monitor:
1. **Response times** (Phoenix traces)
2. **Error rates** (application logs)
3. **User feedback** on response quality
4. **Cost metrics** (OpenAI usage dashboard)

## Success Criteria
- [ ] Configuration updated to `gpt-5.4-2026-03-05`
- [ ] `reasoning_effort: "none"` confirmed in use
- [ ] Application starts without errors
- [ ] Generate Referrals pipeline works end-to-end
- [ ] Generate Action Plan pipeline works end-to-end
- [ ] Phoenix traces show correct model version
- [ ] All backend tests pass
- [ ] All frontend tests pass
- [ ] No regression in response quality

## Documentation Updates
After successful upgrade:
- [ ] Update README if it mentions specific model versions
- [ ] Document any observed performance differences
- [ ] Update team on new model capabilities if relevant

## Timeline
- **Preparation:** 5 minutes (update config files)
- **Testing:** 15-20 minutes (run all tests, manual verification)
- **Deployment:** Immediate (Docker restart)
- **Monitoring:** 24-48 hours post-deployment

## Notes
- This upgrade is backward compatible in terms of API usage
- The `reasoning: {"effort": "none"}` parameter is explicitly supported by GPT-5.4
- No prompt engineering changes needed (same model family)
- Web search functionality should work identically
