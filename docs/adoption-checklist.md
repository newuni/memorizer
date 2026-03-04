# Adoption Checklist

## Technical readiness
- [ ] API reachable behind TLS
- [ ] Worker processing healthy
- [ ] DB backup policy active
- [ ] API keys rotated from defaults

## Product readiness
- [ ] Memory taxonomy agreed (`type`, namespaces, filters)
- [ ] Prompt strategy implemented (`/context` or `/profile`)
- [ ] Write-back policy defined (when to persist)

## Quality readiness
- [ ] Query benchmark set defined
- [ ] Retrieval quality reviewed weekly
- [ ] Latency SLO tracked
- [ ] Hallucination/relevance regressions triaged

## Rollout readiness
- [ ] Canary or shadow mode done
- [ ] Fallback path documented
- [ ] Incident contact/process documented
