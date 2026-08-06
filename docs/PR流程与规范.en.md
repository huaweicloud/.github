# huaweicloud PR Workflow & Standards

> **Language:** English | [中文](./PR流程与规范.md)

## Full Workflow

```
Issue created
    ↓
Issue Bot → auto-classify labels + assign owner + email notify
    ↓
Create Feature Branch → git checkout -b feat/xxx
    ↓
Develop → commit + push
    ↓
New Pull Request (Fixes #N)
    ↓
┌─────────────────────────────────────────────┐
│ CI auto-triggers                             │
│   ├── lint : code style check                │
│   ├── test : automated tests                 │
│   └── build : build verification             │
│                                              │
│ Status Transition auto-triggers              │
│   └── Issue marked status/in-progress        │
│                                              │
│ CODEOWNERS auto-assigns Reviewer             │
│                                              │
│ Need 2 Approvals (branch-protected repos)    │
│   ├── old Approvals invalidated on new commit│
│   └── Code Owner must review                 │
│                                              │
│ ※ Branch protection auto-enabled only for    │
│   new public repos; private & existing repos │
│   have no such enforcement                   │
└─────────────────────────────────────────────┘
    ↓
CI green + 2 Approvals + conversations resolved
    ↓
Merge PR
    ↓
Issue auto-closes → status/resolved
```

---

## 1. PR Standard Configuration

### Branch Protection

> **Scope**: auto-enabled on **new public repositories** at creation (`setup_branch_protection` in `repo_creator.py`).
> - **Private repos**: Free plan limitation, cannot configure branch protection; auto-skipped.
> - **Existing repos**: not batch-configured; enable manually in Settings → Branches if needed.

| Config | Value | Description |
|--------|-----|------|
| Required Approvals | 2 | Cannot approve your own PR |
| Code Owner Review | Required | Owners in CODEOWNERS must review |
| Dismiss stale reviews | On | Old approvals invalidated on new commit |
| Branch up-to-date | strict mode | Checks not behind main before merge |
| Force push | Blocked | `git push -f` prevented |
| Branch deletion | Blocked | main branch cannot be deleted |
| Direct push to main | Blocked | Must go through PR |

### Common Config (all repos)

| Config | Value | Description |
|--------|-----|------|
| CI Pipeline | lint → test → build | .github/workflows/ci.yml |
| Signed commits | Off (temporarily) | Enable after configuring GPG for bots |

---

## 2. CI Pipeline (.github/workflows/ci.yml)

```
pull_request → main branch
    ↓
┌───────┐    ┌───────┐    ┌───────┐
│ lint  │ → │ test  │ → │ build │
└───────┘    └───────┘    └───────┘
```

| Job | Purpose | Configuration |
|-----|------|---------|
| `lint` | Code style/format check | Per language: Python→ruff, JS→eslint, Go→golangci-lint |
| `test` | Automated tests | Python→pytest, JS→npm test, Go→go test |
| `build` | Build verification | Python→pip install, JS→npm build, Go→go build |

If any stage fails, the whole CI turns red and cannot merge.

### Language CI Templates

**Python**
```bash
pip install ruff pytest
ruff check .
pytest
```

**JavaScript/TypeScript**
```bash
npm ci
npx eslint .
npm test
npm run build
```

**Go**
```bash
golangci-lint run ./...
go test ./...
go build ./...
```

---

## 3. Review Standards

### Who Can Review

| Role | Permission |
|------|------|
| Org member | Can Approve / Request Changes / Comment |
| Code Owner | Must review (must approve before merge) |
| PR author | Cannot approve their own PR |

### Review Status

| Status | Description |
|------|------|
| `REVIEW_REQUIRED` | 2 approvals not yet satisfied |
| `APPROVED` | Conditions met, waiting for CI |
| `CHANGES_REQUESTED` | Changes requested, needs re-review |
| `DISMISSED` | Old approvals invalidated after new commit |

### Review Actions

1. Open PR → **Files changed** tab
2. Review the changes
3. Click green **Review changes** button
4. Choose:
   - **Comment** — general comment
   - **Approve** — approve
   - **Request changes** — request modifications
5. Fill in comment → **Submit review**

### Approval Invalidation Rule

When the PR author pushes a new commit, all existing Approvals are auto-invalidated and need re-approval.

---

## 4. CODEOWNERS

`.github/CODEOWNERS` defines code owners:

```codeowners
# Global default reviewer
* @huaweiclouddev

# By directory
/api/          @huaweiclouddev
/frontend/     @huaweiclouddev
/docs/         @huaweiclouddev
/.github/      @huaweiclouddev
```

CODEOWNERS are auto-requested for review when a PR is created.

---

## 5. Issue-PR Linking

| PR Action | Issue Change |
|---------|-----------|
| PR created with `Fixes #N` in description | Issue marked `status/in-progress` |
| PR merged | Issue auto-closed + marked `status/resolved` |

### Supported Closing Keywords

```
close #19  closes #19  closed #19
fix #19    fixes #19   fixed #19
resolve #19 resolves #19 resolved #19
```

---

## 6. Commit Standards

### Commit Message Format

```
<type>: <short description>

<type> values:
  feat     : new feature
  fix      : bug fix
  docs     : documentation
  style    : code format (no functional change)
  refactor : refactor
  test     : tests
  chore    : build/tooling
  ci       : CI config
```

Examples:
```
docs: add Chinese quickstart to README
fix: resolve API timeout issue
feat: add user login module
```

### Signed Commits (to be enabled)

```
git config --global user.signingkey <KEY_ID>
git commit -S -m "feat: xxx"
```

---

## 7. When PR Cannot Be Merged

> Branch-protection-related restrictions (Approvals/Code Owner/strict) are enforced on **branch-protected repos** (new public repos); private and non-protected repos only have CI blocking, other rules are manual.

| Reason | Manifestation |
|------|------|
| CI failed | `lint`/`test`/`build` any red |
| Not enough Approvals (protected only) | need 2, currently 0-1 |
| Code Owner not reviewed (protected only) | owners of specified dirs not approved |
| Branch outdated (protected strict) | needs rebase on main |
| Approvals invalidated (protected only) | new commit pushed, re-approval needed |
| Missing signature | (not yet enabled) |

---

## 8. PR Template

Organization-level template at `huaweicloud/.github/.github/PULL_REQUEST_TEMPLATE.md`.

> **Note**: GitHub's org-level default template is only auto-injected when creating repos via Web UI. Repos created via the creation process (API) don't get it automatically; `repo_creator.py` injects `.github/PULL_REQUEST_TEMPLATE.md` at creation.

Recommended template:

```markdown
## Change Summary
<!-- describe what changed -->

## Related Issue
Fixes #N

## Testing
- [ ] Unit tests passed
- [ ] Manual testing passed

## Checklist
- [ ] Code follows standards
- [ ] Docs updated
- [ ] CI passed
```

---

## 9. Quick Commands

```powershell
# Create Issue
gh issue create -R huaweicloud/<repo> --title "title" --body "body"

# Create PR (link Issue in description)
gh pr create -R huaweicloud/<repo> --title "feat: xxx" --body "Fixes #N" --base main

# View PR status
gh pr view <N> -R huaweicloud/<repo> --json mergeStateStatus,reviewDecision

# View CI checks
gh pr checks <N> -R huaweicloud/<repo>

# Approve PR
gh pr review <N> -R huaweicloud/<repo> --approve

# Merge PR (when conditions met; created repos are squash-only)
gh pr merge <N> -R huaweicloud/<repo> --squash --delete-branch

# Force merge (admin, skip Approvals/CI)
gh pr merge <N> -R huaweicloud/<repo> --squash --admin --delete-branch
```
