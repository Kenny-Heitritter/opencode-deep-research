# M3 Implementation Dependency Analysis

## Task Description
Implement M3 (Verification + Critique) features:
1. Paragraph support spot checks (task 16)
2. Contradiction detection (task 17)  
3. Critique agent (task 18)
4. Cancel mid-run with partial artifacts (task 19)
5. Replay mode for reproducing reports

## Current State

### M0 (Foundation) - COMPLETED
- `/deep-research` command template ✓
- `deep-research-intake` agent ✓
- `deep_research_ui` plugin tool ✓
- MCP server skeleton ✓

### M1 (Research Loop + Artifacts) - PARTIAL
- Task 6 (web search/fetch/extract): marked closed but only skeleton exists
- Task 7 (Notes data model): open, not implemented
- Task 8 (Draft AST structure): open, not implemented  
- Task 9 (artifact directory layout): marked closed but only skeleton exists
- Task 10 (report.md renderer): open, not implemented

### M2 (Competition System) - NOT IMPLEMENTED
- Task 11 (llm-reasoners integration): open, not implemented
- Task 12 (outline competition): open, not implemented
- Task 13 (query competition): open, not implemented
- Task 14 (draft competition): open, not implemented
- Task 15 (effort knob scaling): open, not implemented

### M3 (Verification + Critique) - REQUIRED
- Task 16 (paragraph spot checks): open
- Task 17 (contradiction detection): open
- Task 18 (critique agent): open
- Task 19 (cancel mid-run): open
- Replay mode: not in spec, but mentioned in acceptance criteria

## Dependency Analysis

### M3 Requires:
1. **Paragraph spot checks**: Need paragraphs with citations from report.md
   - Requires: Draft AST (task 8), report renderer (task 10)
   
2. **Contradiction detection**: Need statements across report to analyze
   - Requires: Draft AST (task 8), report renderer (task 10)
   
3. **Critique agent**: Need report with citations to critique
   - Requires: All of M1 + research execution system
   
4. **Cancel mid-run**: Need long-running research job to cancel
   - Requires: Full research pipeline (M1 + M2)
   
5. **Replay mode**: Need saved artifacts to replay
   - Requires: Artifact generation (task 9), research execution system

### Critical Missing Infrastructure:
- Notes data model with spans and provenance (task 7)
- Draft AST structure (task 8)
- Report renderer with citations (task 10)
- Competition system generating reports (tasks 11-15)
- Actual research execution pipeline

## Conclusion

M3 implementation is **BLOCKED** by M1 and M2 dependencies. The verification and critique features require:
1. Report content (paragraphs, citations) to verify
2. Artifact structure to save/load for replay
3. Running research jobs to cancel mid-run

Without the foundational M1/M2 infrastructure, M3 features cannot be meaningfully implemented.