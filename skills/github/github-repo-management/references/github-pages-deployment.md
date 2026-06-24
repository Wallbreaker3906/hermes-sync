# GitHub Pages Deployment — Alternative Methods

When `git push` to `github.com` times out or fails (common in certain network
environments), the GitHub REST API (`api.github.com`) often still works. Use
these API-based methods to deploy static sites.

## Pattern 1: Contents API Upload

Upload files directly to a repo via the Contents API — bypasses `git push`
entirely. Works when `api.github.com` is reachable but `github.com:443` is not.

```python
import urllib.request, json, os, base64

token = os.environ["GITHUB_TOKEN"]
username = "owner"
repo = "repo-name"
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

# Read and base64-encode the file
with open("index.html", "rb") as f:
    content_b64 = base64.b64encode(f.read()).decode()

data = json.dumps({
    "message": "commit message",
    "content": content_b64,
    "branch": "main"
}).encode()

req = urllib.request.Request(
    f"https://api.github.com/repos/{username}/{repo}/contents/index.html",
    data=data, headers=headers, method="PUT"
)
with urllib.request.urlopen(req, timeout=30) as resp:
    print(json.loads(resp.read())["content"]["html_url"])
```

To **update** an existing file, include the `sha` from the previous upload:

```python
# First GET the file to get its sha
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as resp:
    sha = json.loads(resp.read())["sha"]

# Then PUT with the sha
data = json.dumps({
    "message": "update",
    "content": content_b64,
    "branch": "main",
    "sha": sha
}).encode()
```

## Pattern 2: Enable GitHub Pages via API

```python
pages_data = json.dumps({
    "source": {"branch": "main", "path": "/"}
}).encode()

req = urllib.request.Request(
    f"https://api.github.com/repos/{username}/{repo}/pages",
    data=pages_data, headers=headers, method="POST"
)
# 409 = already exists, try PUT instead
# 422 = already configured
```

The Pages site will be at: `https://{username}.github.io/{repo}/`

## Pattern 3: SSH Fallback

When HTTPS to `github.com:443` fails but SSH to `github.com:22` works:

```bash
# Generate an ed25519 key
ssh-keygen -t ed25519 -C "hermes-deploy" -f ~/.ssh/id_ed25519_hermes -N ""

# Add the public key to GitHub (via API or manually)
cat ~/.ssh/id_ed25519_hermes.pub
# → Add at https://github.com/settings/ssh/new

# Use SSH remote
git remote set-url origin git@github.com:owner/repo.git
git push -u origin main
```

If port 22 is also blocked, use SSH over HTTPS port:
```
# ~/.ssh/config
Host github.com
    Hostname ssh.github.com
    Port 443
```

## Pattern 4: Token Scope Issues

Fine-grained tokens need specific permissions for the Contents API:
- **Classic token**: needs `repo` scope
- **Fine-grained token**: needs `Contents: Read and write` permission on the specific repo

Verify token scopes:
```python
req = urllib.request.Request("https://api.github.com/user", headers=headers)
with urllib.request.urlopen(req) as resp:
    print(resp.headers.get("X-OAuth-Scopes", "no scopes header"))
```

Common pitfalls:
- Token works for `/user` but returns 401 for `/repos/.../contents` → likely a fine-grained token without Contents permission
- 422 on Pages API → Pages already enabled, or branch doesn't exist yet
- `main` branch doesn't exist yet → Contents API creates it on first commit with `branch: "main"`
