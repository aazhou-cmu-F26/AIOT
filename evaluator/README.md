# Evaluator-only materials

This directory is host-side and must never be bind-mounted into `blackbox` or
`whitebox`.

The independent evaluator keeps:

- the historical vulnerability identity
- the hidden matching rule (`ORACLE.md`)
- any later privileged diagnostics from an instrumented replica
- the final verdict appended onto an analyst run's `verdict.md`

Analysts submit saved inputs, traces, and explanations. The evaluator applies
the same rule to both viewpoints.
