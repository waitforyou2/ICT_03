# CodeGraph Playbook

Use the pinned official CodeGraph CLI installed by `work/setup.sh`. Disable telemetry through the environment variables set by that script or set:

```bash
export CODEGRAPH_TELEMETRY=0
export DO_NOT_TRACK=1
export CODEGRAPH_NO_DAEMON=1
```

Always pass the exact code root. Initializing the parent workspace causes root confusion and incomplete queries.

```bash
codegraph init "$CODE_ROOT"
codegraph status "$CODE_ROOT"
codegraph files --path "$CODE_ROOT" --max-depth 3
```

## Query order

Prefer narrow, structured operations before semantic exploration:

1. `query <term> --path "$CODE_ROOT" --limit 20 --json`
2. `node <symbol> --path "$CODE_ROOT"`
3. `callers <symbol> --path "$CODE_ROOT"`
4. `callees <symbol> --path "$CODE_ROOT"`
5. `impact <symbol> --path "$CODE_ROOT" --depth 2 --json`
6. `affected <changed-files> --path "$CODE_ROOT" --json`
7. `explore "<anchored behavior question>" --path "$CODE_ROOT" --max-files 6`

Do not start with broad `explore` queries. It returns verbatim source and can consume excessive context. Anchor every exploration to a contract, symbol, event, route, or module, and cap included files.

## Useful repair questions

- Which controller method reaches this service and what response status does it return?
- Who calls this state mutation, and can another path bypass the guard?
- Which listeners consume this event, and are failures isolated from the publisher transaction?
- Does this module import or inject another module's repository or entity?
- Which tests and public entry points are affected by changing this symbol?
- Is there an alternate implementation that defeats a “missing behavior” claim?

After edits:

```bash
codegraph sync "$CODE_ROOT"
codegraph affected --path "$CODE_ROOT" --stdin --json < changed-files.txt
```

Before final handoff, capture necessary graph evidence in the report and remove the index with `codegraph uninit "$CODE_ROOT"`.
