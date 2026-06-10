# Strip Claude Attribution

Remove all `Co-Authored-By: Claude` trailers from every commit in a GitHub repo, then force-push all affected branches.

## Usage

```
/strip-claude <github-repo-url-or-owner/repo>
```

Examples:
- `/strip-claude rkn2/energyInfrastructure`
- `/strip-claude https://github.com/rkn2/myrepo`

## Steps to follow

Given the repo argument `$ARGS`:

1. **Parse the repo** — accept either a full GitHub URL or `owner/repo` shorthand. Normalize to SSH form `git@github.com:owner/repo.git`.

2. **Clone to a temp dir**:
   ```
   REPO_DIR=/tmp/strip-claude-$(date +%s)
   git clone <ssh-url> $REPO_DIR
   ```

3. **Fetch all remote branches** and check them out locally:
   ```
   cd $REPO_DIR
   git fetch --all
   for branch in $(git branch -r | grep -v HEAD | sed 's|origin/||'); do
     git checkout -b $branch origin/$branch 2>/dev/null || true
   done
   git checkout main 2>/dev/null || git checkout master 2>/dev/null || true
   ```

4. **Scan for Claude trailers** — report how many commits on each branch have `Co-Authored-By: Claude`:
   ```
   git log --all --format="%H %D" | while read hash refs; do
     body=$(git log -1 --format="%b" $hash)
     if echo "$body" | grep -q "Co-Authored-By: Claude"; then
       echo "$hash"
     fi
   done
   ```
   Show the user a summary: N commits affected across these branches.

5. **If 0 commits found**, tell the user the repo is already clean and stop.

6. **Run git-filter-repo** to strip all Claude trailers from all local branches:
   ```
   BRANCHES=$(git branch | sed 's/\*/ /' | tr -d ' ' | tr '\n' ' ')
   /Users/becca/Library/Python/3.9/bin/git-filter-repo --force \
     --refs $(git branch | sed 's/\*/ /' | xargs -I{} echo "refs/heads/{}") \
     --message-callback '
   import re
   return re.sub(rb"\n?Co-Authored-By: Claude[^\n]*", b"", message).rstrip() + b"\n"
   '
   ```

7. **Verify** — confirm no Claude trailers remain in `--branches`:
   ```
   git log --branches --format="%b" | grep -i "Co-Authored-By: Claude" || echo "Clean"
   ```

8. **Show the user** a preview of a few rewritten commit subjects and ask for explicit confirmation before pushing.

9. **On confirmation**, force-push all branches:
   ```
   for branch in $(git branch | sed 's/\*/ /'); do
     git push origin $branch --force
   done
   ```

10. **Verify remote** — fetch and confirm no Claude trailers remain on origin.

11. **Clean up** temp dir: `rm -rf $REPO_DIR`

12. Report done: N commits cleaned across M branches.
