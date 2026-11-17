#!/usr/bin/env sh
# Applies branch protection + merge settings. Requires admin on the repo.
# Owner: Fredprime. Run from the repo root: sh scripts/protect-branches.sh
set -e
REPO=${REPO:-Fredprime/EcoWatch}

echo "== repo merge settings =="
gh api -X PATCH "repos/$REPO" \
  -f allow_squash_merge=true \
  -f allow_merge_commit=false \
  -f allow_rebase_merge=false \
  -f delete_branch_on_merge=false \
  --jq '{allow_squash_merge,allow_merge_commit,allow_rebase_merge,delete_branch_on_merge}'

# main — sacred: linear history, rules apply to admins too.
echo "== protect main =="
gh api -X PUT "repos/$REPO/branches/main/protection" --input - <<'JSON'
{
  "required_status_checks": { "strict": true, "contexts": ["infra / compose + postgis"] },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
JSON

# master — integration: same gates, admins may bypass.
echo "== protect master =="
gh api -X PUT "repos/$REPO/branches/master/protection" --input - <<'JSON'
{
  "required_status_checks": { "strict": true, "contexts": ["infra / compose + postgis"] },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
JSON

echo "done. branches are NOT auto-deleted on merge, by design."
