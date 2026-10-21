# Task: Implement a Minimal Reproducible Stage 1 Vulnerability Investigation Lab

## Context

We are conducting an academic research project titled "AI-Assisted Vulnerability Discovery for IoT and Embedded Linux."

Our current objective is **Stage 1 only: Traditional Vulnerability Investigation**.

I have attached `TRADITIONAL_VULNERABILITY_INVESTIGATION_PROCEDURE.md`. Read it completely before making implementation decisions. Treat it as the primary methodological specification.

Our selected software target is [libcoap](https://github.com/obgm/libcoap), a C implementation of the CoAP protocol.

We need a reproducible, shareable Docker-based research environment that supports two controlled knowledge viewpoints:

- **Black-box Analyst:** Can interact with the target through its documented CoAP network interface and inspect externally observable behavior. Cannot access target source code, Git history, internal logs, sanitizer output, or debugging tools attached to the target.
- **White-box Analyst:** Can use the same external protocol interface and additionally inspect the approved source revision, perform static analysis, debug the target, and use runtime instrumentation.

Both viewpoints follow the same investigation procedure.

The two environments must enforce their information boundaries through actual resource and permission isolation. Prompt instructions alone are insufficient.

An independent human evaluator will retain ground truth and perform final validation outside the analyst containers.

## Scope and Constraints

Implement the **minimum viable Stage 1 research environment**.

Use Docker Compose, with three primary services:

1. `target` — runs the selected historical libcoap revision as a CoAP/UDP service.
2. `blackbox` — provides network-based investigation tools without access to source or internal diagnostics.
3. `whitebox` — provides source inspection, build, debugging, and dynamic-analysis tools.

Use separate, clean target instances for measured black-box and white-box runs, even if the same Compose service definition is reused.

Do not implement infrastructure for Stage 2 or Stage 3.

Specifically, do not build an AI agent, agent tool APIs, LLM integrations, dashboards, databases, distributed fuzzing clusters, or general-purpose orchestration frameworks.

Keep code and configuration small, readable, and easy for students to maintain.

## Step 1 — Select and Validate the Historical Vulnerability Task

Before finalizing the Docker build, investigate historical libcoap vulnerabilities.

Find a documented vulnerability that satisfies these requirements:

- It affects a known historical libcoap revision.
- It is related to CoAP network/protocol processing.
- It can be triggered through a reachable CoAP network interface, rather than requiring misuse of an internal C API.
- The vulnerable revision can be compiled and run in a Linux container.
- The behavior can be validated using reproducible evidence such as an ASan report, a deterministic protocol-security violation, or another well-defined runtime condition.
- A corresponding fix, advisory, or reliable historical reference exists.

Prefer a manageable vulnerability with a small reproduction surface.

Research at most three promising candidates before selecting one.

Create `docs/TARGET_SELECTION.md`, recording:

- Vulnerability identifier and sources
- Affected libcoap versions
- Exact vulnerable Git commit
- Relevant network-facing component
- Triggerability assessment
- Proposed deterministic validation oracle
- Build dependencies
- Reasons for selecting or rejecting each candidate

Do not assume that a historical issue affecting a libcoap API is remotely reachable.

If no candidate satisfies the requirements, STOP before implementing a vulnerability-specific environment. Report the blocker and recommend a realistic next step. Do not invent a vulnerable commit, PoC, or validation result.

**Information boundary requirement:** Store any ground-truth details, reference PoC, or solution-revealing vulnerability information separately from analyst-facing materials. Ensure the Black-box workspace cannot access them. White-box access to Git history must be restricted to the approved revision and allowed history; exclude later fix commits.

## Step 2 — Implement the Docker Environment

Create a small, documented repository with the necessary Dockerfiles and `compose.yaml`.

Requirements:

- Pin the exact libcoap commit.
- Pin the base image by digest and record compiler/dependency versions.
- Use a documented Linux target architecture.
- Build libcoap from the pinned source revision.
- Start a functioning CoAP/UDP endpoint.
- Provide a working Black-box workspace.
- Provide a working White-box workspace.
- Support repeatable startup, shutdown, and fresh-run reset.
- Avoid unnecessary dependencies and privileged container settings.

If historical libcoap requires an older build system, use the build instructions appropriate for that revision.

Keep Docker configuration readable and avoid unnecessary abstraction.

### Black-box Enforcement

The Black-box environment must:

- Have access to protocol documentation and explicitly approved network-testing tools.
- Reach only the intended CoAP testing endpoint and any strictly required supporting network services.
- Have no source tree, `.git` directory, internal runtime logs, evaluator files, reference PoC, or hidden oracle artifacts.
- Have no Docker socket, privileged mode, or host filesystem access.
- Run as a non-root user with unnecessary privileges removed.
- Have no unrestricted external network access during investigation.
- Be unable to inspect other containers or privileged target diagnostics through the normal analyst workspace.

Use read-only filesystems where practical and explicitly writable directories for test outputs.

Implement negative tests to verify these restrictions.

Document Docker's security limitations. Do not claim protection against someone with administrative control over the host or Docker daemon.

### White-box Environment

The White-box environment must:

- Access the approved libcoap source revision and permitted history.
- Support source browsing and conventional text search.
- Provide C build tools, Clang, AddressSanitizer, and GDB.
- Support static analysis using the available compiler tools.
- Support reproducible internal runtime testing.
- Support libFuzzer if a practical fuzz target can be built for the selected component.

Do not install complex security tools unless they are required by the procedure or target.

The White-box environment must not access evaluator-only ground truth or reference solutions.

## Step 3 — Implement Minimal Investigation Tools

Provide a simple Python-based CoAP/UDP test client that can:

1. Read a binary input packet from a file.
2. Send it to the configured target endpoint.
3. Collect any response or timeout information.
4. Save the raw response, exit status where observable, and relevant timing information.
5. Replay the same saved input.

If the selected vulnerability involves protocol state, support a small sequence of packets with configurable delays and timeouts.

Include a few harmless, valid CoAP inputs for smoke testing.

Provide a simple way to generate or mutate inputs for network testing. Keep this separate from any optional White-box in-process fuzz target.

If libFuzzer is implemented, follow the official LLVM fuzz target convention and provide build and execution instructions.

Do not implement a generic plugin architecture or agent-compatible API.

## Step 4 — Implement Simple Experiment Logging

Use ordinary files and standard formats. Do not introduce a database or telemetry framework.

For each investigation run, create a directory similar to:

```text
results/
  run-001/
    notes.md
    commands.log
    inputs/
    outputs/
    findings.md
```

Record at minimum:

- Run identifier
- Analyst viewpoint
- Target commit and environment/tool versions
- Start time, end time, and elapsed time
- Commands and tools used
- Investigative hypotheses
- Candidate findings
- Failed attempts
- Saved test inputs and observed results
- Reproduction attempts and outcomes
- Manual reasoning and workflow bottlenecks
- Deviations from the experimental protocol

Keep factual runtime observations separate from analyst interpretations.

Store Black-box and White-box artifacts separately. Black-box outputs must not expose internal traces or diagnostics.

Record SHA-256 hashes for saved reproduction inputs.

Allow the independent evaluator to append a final verdict without exposing hidden ground truth to analyst workspaces.

## Step 5 — Documentation

Produce:

- `README.md` — concise setup and Quick Start.
- `docs/TARGET_SELECTION.md` — historical vulnerability selection and supporting references.
- `docs/ENVIRONMENT.md` — Docker architecture, dependencies, tool versions, network boundaries and known limitations.
- `docs/ACCESS_CONTROL.md` — Black-box and White-box permissions and enforcement tests.
- `docs/TESTING.md` — normal packet testing, input replay, optional fuzzing, sanitizer usage, and evidence collection.
- `docs/IMPLEMENTATION_REPORT.md` — what was implemented, what was tested, results, remaining blockers and limitations.

Include the supplied Procedure document under `docs/`, preserving its methodological requirements.

Document concrete commands wherever possible.

A teammate should be able to build the environment and execute a normal CoAP test using only the README and Docker.

## Step 6 — Self-Validation Loop

Use the following Acceptance Checklist as your implementation completion criteria.

For each item:

1. Execute an actual test.
2. Inspect the output and exit status.
3. If the test fails, identify the cause, implement a correction, and rerun it.
4. Save the test command, result and supporting evidence.
5. Mark the item PASS only after successful execution.
6. If blocked, mark it BLOCKED or FAIL and explain why.

Do not mark an item PASS merely because the corresponding code or configuration exists.

### Automated Acceptance Checklist

- [ ] **AC-01:** Docker images build successfully from a clean state.
- [ ] **AC-02:** The selected libcoap target starts and responds to a valid CoAP request.
- [ ] **AC-03:** Black-box can send packets but cannot access target source code or internal runtime logs.
- [ ] **AC-04:** Black-box cannot access Docker socket, unauthorized host resources, evaluator artifacts or unauthorized network destinations.
- [ ] **AC-05:** White-box can inspect approved source code and successfully execute a real debugger and sanitizer test.
- [ ] **AC-06:** At least one saved input can be replayed, producing repeatable observable results.
- [ ] **AC-07:** Investigation logs successfully record viewpoint, tools, timestamps, inputs, commands, outcomes and relevant process measurements.

### Manual Acceptance Checklist

- [ ] **AC-08:** Another team member independently follows the README and successfully reproduces the environment and experiment.

**AC-08 must remain PENDING until we receive actual feedback from another team member. Do not self-certify it.**

Save a concise checklist with PASS/FAIL/BLOCKED/PENDING status, command, evidence, and notes for each criterion.

### Additional Stage 1 Readiness Check

Beyond the infrastructure checklist, report separately whether:

- The historical vulnerability task has been finalized.
- The candidate input reaches the selected network-processing component.
- The claimed behavior has been reproduced.
- The proposed oracle has been executed successfully.
- Runtime evidence has been saved.
- Baseline measurements have been collected.

These are necessary for completing Stage 1 but should not be reported as completed merely because the infrastructure works.

A real analyst investigation and independent evaluator review may still be needed.

## Step 7 — Final Report

When finished, provide:

1. A concise architecture summary.
2. The selected historical libcoap vulnerability and pinned commit, supported by sources.
3. The complete implemented file tree.
4. Exact build and run commands.
5. The Acceptance Checklist with actual results.
6. Tests and experiments executed, with saved evidence locations.
7. Known limitations, unresolved blockers and any deviations from the Procedure.
8. Specific instructions for the independent teammate validation step.

Do not claim that a test passed unless it actually ran successfully.

If Docker execution is unavailable in your environment, distinguish implemented code from unverified behavior. Leave the affected acceptance items BLOCKED.

## Working Instructions

Work autonomously on the implementation and verification, within the approved repository.

Begin by inspecting the repository and reading the attached Procedure specification. Give a short implementation plan before modifying files.

Prioritize correctness, reproducibility, and clarity over extensibility.

Keep the implementation focused on Stage 1.

Iterate until AC-01 through AC-07 pass or until remaining blockers are documented with evidence.

Do not wait for additional confirmation for ordinary, reversible repository changes and local tests. Ask before making security-sensitive external changes, publishing vulnerability details, changing access permissions outside the project, or performing destructive operations.

At the end, show precisely what is ready for teammates and what still requires their independent verification.
