# ML Workflow Template Documentation Structure

## Recommended Approach

**Template Type**: **Project-agnostic patterns with full reference implementations**
- Provide abstract patterns that I adapt per project
- Include complete working implementations as copy-paste starting points
- Best of both: flexibility + concrete examples

**Storage**: **Single file: `claude-d6tflow-ml.md`**
- One comprehensive ML workflow reference (not split by task type)
- Easier for me to reference one place vs multiple files
- Follows existing pattern (one `claude-d6tflow.md`, not multiple files)

**Structure**: **Tiered approach - Quick patterns + Full implementations**

```
claude-d6tflow-ml.md structure:

## ML Workflow Overview
- Task dependency chain diagram
- When to use each task type

## Quick Reference Patterns (Token-Efficient)
### ModelTrain
[Concise skeleton with key concepts]

### ModelPredict
[Concise skeleton]

### ModelEvalIS/OS
[Concise skeletons]

### ModelSHAP
[Concise skeleton]

## Full Implementation Templates (Copy-Paste Ready)
### ModelTrain - Complete Implementation
[Full working code like your ModelPerformanceIS example]

### ModelPredict - Complete Implementation
[Full working code]

### ModelEvalIS - Complete Implementation
[Full working code]

### ModelEvalOS - Complete Implementation
[Full working code with cross-validation]

### ModelSHAP - Complete Implementation
[Full working code with explainer + feature importance]

## Adaptation Checklist
- [ ] Update feature column selection
- [ ] Update target variable name
- [ ] Update model hyperparameters
- [ ] Update metrics for problem type
- [ ] Update SHAP analysis for model type
```

## Implementation Plan

1. **Create `claude-d6tflow-ml.md`** with:
   - Quick reference section (I scan this first)
   - Full implementations section (I copy from here)
   - Adaptation checklist (reminds me what to customize)

2. **Update `CLAUDE.md`** to reference:
   ```
   @claude-d6tflow-ml.md
   ML workflow patterns (training, prediction, evaluation, SHAP)
   ```

3. **Document in each `claude-project.md`**:
   - Which ML tasks are implemented
   - Project-specific customizations made
   - Deviations from standard templates

## Why This Works Best

✅ **One reference file**: Easy for me to find patterns
✅ **Tiered structure**: Quick scan + deep dive when needed
✅ **Copy-paste ready**: Your full implementations as starting points
✅ **Adaptation guidance**: Checklist ensures I customize correctly
✅ **Token efficient**: Quick reference minimizes context, full examples available when needed
✅ **Consistency**: I follow same patterns across projects
✅ **Flexibility**: Can adapt to project-specific nuances

Ready to create `claude-d6tflow-ml.md` with your ML task templates?
