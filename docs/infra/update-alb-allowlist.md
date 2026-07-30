# Update the pilot ALB IP allow-list

The pilot has wrapped, but its containers are still running and its URL is meant to be reachable only by a small, known group. Access is restricted at the ALB security group level to a manually maintained list of IPv4 addresses (see `infra/modules/service/networking.tf` and the `alb_ingress_cidr_blocks` variable). This doc covers how to add or remove someone from that list.

## Instructions

1. Get the requester's public **IPv4** address. IPv6 won't work — the security group's `cidr_blocks` field only accepts IPv4 CIDRs, and the ALB isn't dualstack, so there's no IPv6 listener to reach anyway. Have them run:

   ```bash
   curl -4 ifconfig.me
   ```

   Don't use a generic "what's my IP" tool/site — on a dual-stack network it may report an IPv6 address instead, which won't work here.

2. Create a new branch off `main`:

   ```bash
   git checkout main
   git pull
   git checkout -b fix/update-alb-allowlist
   ```

3. Add the address (as a `/32` CIDR) to `alb_ingress_cidr_blocks` in **both**:
   - `infra/app/app-config/main.tf`
   - `infra/frontend/app-config/main.tf`

   These are two independent lists kept in sync manually — there's no shared variable, so both files need the same edit.

4. Commit, push, and open a PR:

   ```bash
   git add infra/app/app-config/main.tf infra/frontend/app-config/main.tf
   git commit -m "fix: update pilot ALB allow-list"
   git push -u origin fix/update-alb-allowlist
   gh pr create
   ```

5. Get an approving review and merge. The repo's branch ruleset on `main` requires at least one approval before merge (squash-only).

6. **Merging only auto-deploys `dev`.** `prod` needs a manual deploy — trigger both:

   ```bash
   gh workflow run "Deploy app" -f environment=prod -f version=main
   gh workflow run "Deploy frontend" -f environment=prod -f version=main
   ```

7. Confirm both runs succeed (`gh run list --workflow "Deploy app" --limit 1` / `--workflow "Deploy frontend" --limit 1`), then have the requester test. `referrals.navateam.com` (frontend) and `api.referrals.navateam.com` (backend) are the **prod** domains — testing against a `dev`-only URL doesn't confirm prod is actually locked down.

## Notes

- If someone loaded the page in their browser *before* a prod deploy finishes, their next form submission may fail with `Error: Failed to find Server Action "<id>". This request might be from an older or newer deployment.` That's a stale frontend bundle, not an allow-list problem — a hard refresh fixes it.
- PR preview environments (Terraform workspaces named `p-<PR#>`) and Terratest's ephemeral workspaces (`t-<random>`) are intentionally exempt from this allow-list (see `infra/modules/service/networking.tf`), so they stay reachable from any IP for CI and manual PR review. This is a deliberate tradeoff, not a gap to fix — preview environments are short-lived and get cleaned up automatically.
