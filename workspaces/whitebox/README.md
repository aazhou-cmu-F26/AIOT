# White-box workspace

Use the `whitebox` Compose profile. Source is at `$LIBCOAP_SRC`
(`/home/analyst/src/libcoap`). Build artifacts belong in
`/workspace/scratch/wb-build`.

Do not read `evaluator/` on the host while acting as an analyst.

```sh
docker compose --profile whitebox exec whitebox /opt/lab/tools/whitebox_tool_check.sh
```
