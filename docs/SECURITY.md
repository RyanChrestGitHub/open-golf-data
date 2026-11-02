# Privacy and security posture — prototype

**Do not deploy this bootstrap on a public or commercial computer.** It has no authenticated cloud portal, no per-user encrypted database, no consent/revocation service, no retention policy, and no live input hardening.

## Relevant trust boundaries

1. **Vendor files and recordings are untrusted inputs:** parsers must bound size, validate schema and sandbox unsafe formats.
2. **A facility administrator is not the golfer:** authorization to collect does not imply authorization to publicly share every customer's data.
3. **A login is not attribution:** a verified source participant link or explicit confirmed mapping must establish whose observation is whose.
4. **Local CLI is not a cloud identity service:** users with access to the local DB can run exports. Do not expose the CLI as a remote endpoint.
5. **Fixture attachments are untrusted:** ensure contributor permission and privacy screening before moving evidence into a public repo.
6. **Agents read untrusted prose:** restrict tokens, filesystem and network; never auto-merge prompt-controlled changes or run untrusted CI on a hardware PC.

## Future hosted minimum before real data

Authenticated account tokens; installation enrollment; scoped session permission and consent; encrypted transport; tenant-bound row access; database backup encryption; per-player export/deletion rights; rate limits; audit log; incident response; documented unclaimed-record retention; verified controls against cross-tenant access. Privacy and operator agreement review is required before collecting or transmitting real guest data.
