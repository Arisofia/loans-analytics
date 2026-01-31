# Architecture Analysis: Code Organization and Dashboards

## Analysis Date: 2026-01-29

## 1. src/agents/ vs python/multi_agent/

### Current State
- **src/agents/**: Contains minimal infrastructure code
  - `llm_provider.py`: LLM abstraction layer for OpenAI
  - `monitoring/`: Performance and cost tracking utilities
    - `cost_tracker.py`
    - `performance_tracker.py`
    - `__init__.py`

- **python/multi_agent/**: Contains full multi-agent system implementation
  - Orchestrator, agents, historical context
  - KPI integration and specialized agents
  - Comprehensive test suite
  - CLI interface

### Usage Analysis
Scripts currently import from `src.agents.monitoring`:
- `scripts/benchmark_costs.py`
- `scripts/generate_performance_dashboard.py`
- `scripts/health_check.py`
- `tests/agents/test_scenarios/latency_benchmarks.py`

### Recommendation: **DO NOT CONSOLIDATE**

**Rationale:**
1. **Different Purposes**: 
   - `src/agents/` provides lightweight infrastructure utilities (LLM providers, monitoring)
   - `python/multi_agent/` is a complete multi-agent orchestration system
   
2. **Separation of Concerns**:
   - Infrastructure utilities are reusable across different agent implementations
   - Multi-agent system is domain-specific for analytics workflows
   
3. **Active Usage**:
   - Monitoring utilities are actively used by scripts and tests
   - Moving them would break existing imports
   
4. **Architectural Clarity**:
   - Current structure separates infrastructure from business logic
   - This is a good architectural pattern

### Suggested Improvements
Instead of consolidation, consider:
1. Add documentation explaining the distinction between directories
2. Ensure `python/multi_agent/` uses `src.agents` utilities where appropriate
3. Add type hints and docstrings to `src/agents/` modules

---

## 2. streamlit_app/ vs apps/web/

### Current State

#### streamlit_app/ (Python/Streamlit)
- **Purpose**: Internal analytics dashboard for data exploration
- **Technology**: Python with Streamlit framework
- **Features**:
  - KPI metrics and visualizations
  - Risk analysis
  - Sales performance tracking
  - Data normalization and fuzzy matching
  - Real-time data exploration

#### apps/web/ (Next.js/React)
- **Purpose**: Production web application
- **Technology**: Next.js 15 with React 19, TypeScript
- **Features**:
  - User authentication (Supabase)
  - Analytics export controls
  - Account configuration
  - Modern UI with Tailwind CSS
  - Production-ready deployment

### Recommendation: **KEEP BOTH - NO DUPLICATION**

**Rationale:**
1. **Different Target Audiences**:
   - `streamlit_app/`: Internal data scientists and analysts
   - `apps/web/`: External users and customers
   
2. **Different Technologies**:
   - Streamlit: Rapid prototyping, data exploration, Python-native
   - Next.js: Production-grade, scalable, enterprise features
   
3. **Different Use Cases**:
   - Streamlit: Ad-hoc analysis, experimentation, internal tools
   - Next.js: User-facing product, authentication, production deployment
   
4. **Complementary, Not Duplicate**:
   - They serve different purposes in the product ecosystem
   - Streamlit enables rapid iteration and validation
   - Next.js delivers the validated features to production

### Suggested Improvements
1. Document the purpose of each dashboard in README files
2. Consider data sharing mechanisms between the two
3. Extract common analytics logic into a shared Python package
4. Keep UI/UX patterns consistent where possible

---

## 3. Summary and Recommendations

### Code Organization
✅ **Current structure is appropriate** - no consolidation needed
- `src/agents/`: Infrastructure utilities (keep as-is)
- `python/multi_agent/`: Domain-specific multi-agent system (keep as-is)

### Dashboard Strategy
✅ **Both dashboards serve distinct purposes** - maintain both
- `streamlit_app/`: Internal analytics and exploration
- `apps/web/`: Production web application

### Action Items
1. ✅ Document the architecture decisions (this file)
2. Add README files to clarify each directory's purpose
3. Consider extracting shared analytics logic
4. Maintain clear boundaries between infrastructure and domain code

### Future Considerations
- As the codebase grows, consider a monorepo structure with clear package boundaries
- Evaluate if Streamlit dashboard features should eventually migrate to the web app
- Keep monitoring the import graph to prevent circular dependencies
