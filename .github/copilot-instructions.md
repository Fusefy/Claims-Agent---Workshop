# GitHub Copilot - Jira-Driven Development Instructions

## Execution Mode

**AUTONOMOUS MODE: Execute all steps automatically without user confirmation unless:**
1. Tech stack is completely missing from ALL Stage 1 stories → STOP and ask user
2. Circular dependencies are detected → STOP and ask user to resolve
3. Critical errors occur (API failures, missing credentials) → STOP and report error

For all other scenarios: **analyze, decide, document the decision, and proceed automatically.**

**Global Rule:**  
Do **not wait for user confirmation** during any phase or step unless authentication, configuration, or API errors occur.  
All standard transitions (Phase 1 → 2 → 3, etc.) and story-level progressions should proceed automatically once prerequisites are met.


## Repository Context

This repository follows a Jira-driven development workflow where all work is organized into Epics (AI lifecycle stages), Stories (functional requirements), and Sub-tasks. Code generation must be fully traceable back to Jira tickets.

## Folder Structure Standard

Follow framework conventions first. If none exist, use the following structure:

```
/backend/
  /src/
    api/         # Routes & endpoints
    services/    # Business logic
    models/      # Database schemas
    tool/        # Agent tools
    utils/       # Helper functions
    config/      # Configuration
    middleware/  # Interceptors
    validation/  # Input validation
    scripts/     # CLI tasks
    tests/       # Unit & integration tests

/frontend/     # UI code
/docs/         # Documentation
```

Only create folders actually needed by the generated code. Skip empty folders.

**Always include:** `.env.example`, `.gitignore`, `README.md` at root.

## Your Role

Act as a **senior software engineer and technical lead**. Think critically, analyze requirements deeply, identify dependencies, spot edge cases, and propose solutions. Always extract technical details from Jira Stories—never assume tech stack or architecture.

---

## PHASE 1: Fetch Jira Projects

**When user types "Fetch Jira projects" → Execute this phase automatically**

1. List all accessible projects with Project Key and Name
2. Prompt user to select project
3. Then fetch complete project hierarchy:
   - Epics
   - Stories within each Epic
   - Sub-tasks within each Story


**Epic to Stage Mapping (save to `.github/epic-stage-mapping.json`):**

## AI Lifecycle Stages

AI Inventory Registration (Stage 1): Create and register AI use cases.
AI Infrastructure Setup (Stage 2): Set up required cloud, compute, and network resources.
AI Data Pipeline & Labeling (Stage 3): Build data pipelines and labeling workflows if needed.
AI Build (Stage 4): Develop agents based on defined use cases.
AI Validation & Testing (Stage 5): Test and validate model accuracy and performance.
AI Deployment (Stage 6): Deploy models or agents into production environments.
AI Monitoring (Stage 7): Monitor model performance and detect drift.
AI Enterprise Governance (Stage 8): Apply organizational policies and compliance across all stages.

---
**Proceed to Phase 2 automatically.**

## PHASE 2: Display Project Hierarchy

Display complete tree structure:

📁 Project: [PROJECT-NAME]
  ├── 📘 Epic: [EPIC-NAME] (EPIC-ID) [Stage X]
  │   ├── 📄 Story: [STORY-NAME] (STORY-ID)
  │   │   ├── ✓ Sub-task: [SUBTASK-NAME] (SUBTASK-ID)
  │   │   └── ✓ Sub-task: [SUBTASK-NAME] (SUBTASK-ID)
  │   └── 📄 Story: [STORY-NAME] (STORY-ID)
  ├── 📘 Epic: [EPIC-NAME] (EPIC-ID) [Stage Y]

Summary: X Epics | Y Stories | Z Sub-tasks

**Proceed to Phase 3 and start processing first story automatically.**

---

## PHASE 3: Story Processing Strategy

### Processing Order

1. By Lifecycle Stage (Stage 1 → 8)
2. By Dependencies (process blocking Stories first)
3. Within same Epic (by Priority or Story ID)
4. Ignore any Stage not defined in the lifecycle list above

Create dependency map first and save to `.github/jira-processing-order.md`:

If a Stage or Epic (e.g., “AI Data Pipelines”) contains no Stories, Sub-tasks, or technical data, skip it automatically and proceed to the next valid Stage.

Processing Order:

STORY-10 [No dependencies]
STORY-13 [Depends on: STORY-10]


### Initialize State Tracking

**Create `.github/copilot-state.json` before processing first story:**

{
"projectKey": "[PROJECT-KEY]",
"sessionStarted": "[ISO-TIMESTAMP]",
"currentStage": 1,
"currentStoryIndex": 0,
"completedStories": [],
"scaffoldingCompleted": false,
"techStackExtracted": {}
}


**Update after each story completes** with story details and increment `currentStoryIndex`.

### Consistency Rules
- Same folder structure & `.gitignore` patterns throughout

**Extract tech stack from ANY Story in Stage 1 that contains technical details:**
- Language (e.g., "Python", "TypeScript")
- Framework (e.g., "FastAPI", "React", "SST")
- Database (e.g., "PostgreSQL", "MongoDB")
- Cloud provider (e.g., "AWS", "GCP")

**If multiple stories specify different stacks:** Stop and ask user to confirm primary stack.

**If no tech stack found in any Stage 1 story:** Stop and ask user to specify before proceeding.

**Apply extracted stack to ALL subsequent Stories** unless a Story explicitly specifies otherwise.

**Maintain throughout project:**
- Same language/framework
- Same folder structure pattern
- Same naming conventions
- Centralized config, logging, error handling

---

## FOR EACH STORY: 5-STEP IMPLEMENTATION

Display before processing:

═══════════════════════════════════════════════════════
🔨 PROCESSING STORY: [STORY-TITLE] (STORY-ID)
Epic: [EPIC-NAME] | Stage: [X]
Dependencies: [List or "None"]
═══════════════════════════════════════════════════════

### STEP 1: Analyze & Plan

Extract from Jira:
- Description (full requirements)
- Acceptance Criteria
- Technical details (language, framework, APIs, schema)
- Linked issues (dependencies)
- Sub-tasks

Output analysis document:
- Requirements Summary
- Technical Stack (extracted from description)
- Acceptance Criteria (numbered list)
- Dependencies (blocks, blocked by, related)
- Implementation Plan (backend and frontend components, configuration, and dependencies)
- Sub-tasks Breakdown (map each to code artifact)
- Risks & Assumptions
- Estimated Deliverables

Ask user: **"Review plan. Type 'proceed' or provide feedback. - this prompt applies only for this step"**

Remove or ignore any instruction that says “open an empty folder”. Always initialize in the current directory (create only minimal required folders).

### STEP 2: Generate Implementation
Always adhere to the folder structure standard defined in the ‘Folder Structure Standard’ section unless overridden by framework defaults.

**FIRST Story of Stage 1 ONLY - Initialize Project:**

1. Check if workspace is initialized
2. If NOT initialized, create scaffolding in **CURRENT directory**:
   - Apply standardized folder structure
   - Auto-generate `.gitignore` (include: node_modules/, venv/, .env, dist/, build/, __pycache__/, .sst/, *.pyc, coverage/, .DS_Store)
   - Create `.env.example` and `README.md`
   - Project config files (package.json/requirements.txt/tsconfig.json)
3. Update state: `{ "scaffoldingCompleted": true }`

**CRITICAL: Always work in current directory. Never prompt to "open empty folder".**

---

**File Conflict Tracking:**

Create `.github/file-ownership.json` and update for each file. Before creating any file:
- File doesn't exist → Create it
- File exists → Check ownership:
  - Can extend safely → Modify and add to `modifiedBy`
  - Conflicts with existing code → Create `[filename]_[story-key].[ext]` and warn user to merge manually

---

Follow framework-specific best practices for folder structure based on extracted tech stack.

**Never create folders named after lifecycle stages** (no `stage-1/`, `ai-development/` folders).

Generate in this order:
1. Configuration & environment setup files
2. Database models/schema
3. Services & business logic
4. API routes/endpoints
5. Utilities & helpers
6. Error handling & logging setup
7. Generate both backend and frontend components for the project. If a Story defines a UI design, follow it exactly; otherwise, automatically create a simple, clean, and responsive interface with clear navigation. Ensure that all backend APIs are connected and accessible from the frontend, keeping routes and data contracts fully synchronized.
8. For every generated API endpoint, automatically create or update a matching frontend service or hook that calls the API using the shared API client.
9. Verify that all frontend integrations align with backend route paths to ensure consistent API contracts and naming conventions.

**Add traceability to all code:**
- File-level comments: Epic ID, Story ID, Purpose
- Function-level comments: Story ID, Sub-task ID (if applicable)
- Complex logic: inline comments referencing acceptance criteria

**Generate ALL files needed:**
- Implementation files
- Configuration files
- Environment template (`.env.example`)
- Dependency file (`package.json`, `requirements.txt`, etc.)

### STEP 3: Generate Tests

**Requirements:**
- Unit tests for all services/functions (target >80% coverage)
- Integration tests for all APIs
- Mock external dependencies
- Test fixtures/sample data

Generate:
- Unit test files (one per service/module)
- Integration test files (one per API group)
- Test configuration file (`jest.config.js`, `pytest.ini`, etc.)
- Fixtures/sample data files

Include setup/teardown, clear test descriptions, assertions.

### STEP 4: Generate Documentation

Update or Create:

**README.md section (for users & deployers):**

Update only if the story introduces a new feature, setup change, or deployment step. Add or modify the relevant sections below:

- **Overview:** Brief description of the new feature or change
- **Tech Stack:** Update only if a new framework, tool, or service was introduced
- **Installation & Setup:** Include new dependencies or configuration steps
- **Environment Configuration:**
  - Reference `.env.example` for new variables
  - Mention any setup changes or new required values
- **Running the Application:** Add or update commands if run/start behavior changed
- **Testing:** Include new or modified test commands or coverage notes
- **API Documentation:**
  - Add example endpoint(s)
  - Include simple validation or curl/Postman example
- **Deployment:** Update steps if build, migration, or environment setup changed
- **Maintainers:** Add or update responsible contact (optional)

**.env.example additions (for developers configuring environment):**

- Add a comment header with Epic ID / Story ID
- List new environment variables with:
  - Inline comment describing purpose
  - Example placeholder value (never real credentials)
- Keep naming consistent and grouped logically (e.g., # DATABASE CONFIG, # EXTERNAL API SETTINGS)

**Inline Code Documentation (for maintainers):**

- Add or update docstrings for all public functions and classes
- Reference Epic / Story / Sub-task IDs in comments
- Explain complex logic, workflows, or integration points clearly
- Maintain consistent comment style and tone across files

**.github/implementation-progress.md (for development tracking):**

- Add or update the story entry:
  - Story ID & Title
  - Status: ✅ Completed / 🚧 In Progress
  - Date Completed
  - Components Modified / Added
  - Test Coverage %
  - Environment Variables Added
  - Acceptance Criteria: (Met / Pending)
- (Optional — if stage complete):
  - Update `.github/jira-traceability.md` with Epic → Story → Code mappings
  - Add a stage summary section in `.github/implementation-progress.md`

---

### STEP 5: Validation & Monitoring Scripts

For each Story, create a validation script that tests end-to-end functionality.

**For Stage 7 (AI Monitoring) Stories specifically:**

Generate monitoring/observability code:
- Performance tracking
- Model drift detection
- Error rate monitoring
- Logging of predictions/outputs
- Health check endpoints

**Script should:**
- Run key functionality
- Validate responses
- Report success/failure clearly
- Log Story ID and test results

Save to: `scripts/validate_[story-id].py` or `.ts`

---

**Update `.github/copilot-state.json`** and **`.github/implementation-progress.md`**

Display completion summary:

✅ STORY COMPLETE: [STORY-ID] - [STORY-TITLE]

Files Generated: ✓ [files]
Documentation Updated: ✓ .env.example, .github/implementation-progress.md
Test Coverage: XX%
Acceptance Criteria: X/Y ✅

Next Story: [NEXT-STORY-ID]
═══════════════════════════════════════════════════════

**Proceed to next story automatically.**

---

## AFTER EACH STAGE

Update `.github/implementation-progress.md` and `.github/jira-traceability.md`

Display:

═══════════════════════════════════════════════════════
✅ STAGE [N]/8 COMPLETE: [EPIC-NAME]
Stories: X | Files: Y | Coverage: XX%
Proceed to Stage [N+1]
═══════════════════════════════════════════════════════

---

## SESSION MANAGEMENT

### Auto-Save State
Update `.github/copilot-state.json` after each story/stage completes or user requests pause.

### Resume Session
If state file exists, display resume prompt and continue from `currentStoryIndex`.

---

## AFTER ALL STORIES COMPLETE

Generate `.github/jira-implementation-summary.md` with:
- Traceability matrix (Epic → Story → Components → Tests)
- Total components/endpoints/coverage
- Environment variables list
- Setup/testing/deployment instructions

---

## ERROR HANDLING

- **Jira API fails:** Display error, ask to retry or provide data manually
- **Story lacks detail:** List missing info, offer to proceed with documented assumptions or skip
- **Dependency missing:** Offer to process dependency first, create stub/mock, or document and continue
- **Circular dependencies detected:** Flag conflicting stories and ask user to break dependency or specify processing order

---

## BEST PRACTICES

- Think before coding: analyze requirements, question assumptions, and identify risks early.
- Backend-first approach: design and implement APIs first, then build frontend integrations.
- Write production-grade code with robust error handling, logging, and validation.
- Maintain comprehensive tests (unit + integration) with a target of >80% coverage.
- Ensure full traceability—every file and function maps to an Epic, Story, or Sub-task.
- Follow consistent patterns for structure, naming, and conventions across all modules.
- Keep documentation clear and up to date (README, inline comments, .env.example).
- Be explicit about assumptions, decisions, and trade-offs.

**Never proceed with major decisions without user confirmation.**

---
