# GitHub Security Features Setup

This guide explains how to enable and configure GitHub's security features for the SMTPy repository.

## Overview

The CI/CD pipeline includes security scanning using Trivy, which can upload results to GitHub's Security tab. However, this requires enabling Code Scanning in your repository settings.

## Current Status

✅ **Security Scanning**: Trivy scans are running in CI/CD
⚠️ **Code Scanning**: Needs to be enabled (see below)
✅ **Artifact Upload**: Results saved as workflow artifacts
✅ **Summary Display**: Vulnerability counts shown in workflow summary

## Enable GitHub Code Scanning

### Option 1: Enable via Web UI (Recommended)

1. **Navigate to Repository Settings**
   - Go to your repository: `https://github.com/larrymotalavigne/smtpy`
   - Click on **Settings** tab

2. **Enable Code Scanning**
   - In the left sidebar, click **Security & analysis** (under "Security")
   - Scroll to **Code scanning**
   - Click **Set up** → **Advanced**

3. **Configure Code Scanning**
   - GitHub will offer to create a `codeql-analysis.yml` workflow
   - You can either:
     - **Option A**: Accept the default CodeQL workflow (recommended)
     - **Option B**: Skip this and just enable the feature for Trivy uploads

4. **Verify Enablement**
   - Go to the **Security** tab
   - You should now see **Code scanning** section
   - Your Trivy results will appear here after the next workflow run

### Option 2: Enable via GitHub Advanced Security

If you have GitHub Advanced Security enabled:

1. Go to **Settings** → **Security & analysis**
2. Enable **GitHub Advanced Security**
3. Enable **Code scanning**
4. Enable **Secret scanning** (recommended)
5. Enable **Dependency review** (recommended)

### Option 3: Contact Repository Admin

If you don't have admin access:

1. Ask a repository administrator to enable Code Scanning
2. Share this document with them
3. They can follow Option 1 or Option 2 above

## Verify Security Features

After enabling Code Scanning, verify it works:

1. **Trigger a workflow run**
   ```bash
   git commit --allow-empty -m "test: trigger security scan"
   git push
   ```

2. **Check the workflow**
   - Go to **Actions** tab
   - Wait for the `security-scan` job to complete
   - Should see: ✅ "Upload Trivy results to GitHub Security tab"

3. **View results**
   - Go to **Security** tab → **Code scanning**
   - You should see alerts from Trivy (if any vulnerabilities found)

## Understanding Security Scan Results

### Viewing Results

#### In GitHub Security Tab

Once Code Scanning is enabled:
- **Security** → **Code scanning** shows all vulnerabilities
- Filter by severity, status, or tool (Trivy)
- Click on an alert for detailed information and remediation advice

#### In Workflow Artifacts

Results are always available as artifacts (even if Code Scanning is disabled):
1. Go to **Actions** → Select a workflow run
2. Scroll to **Artifacts** section
3. Download `trivy-results` (SARIF format)
4. View with a SARIF viewer or text editor

#### In Workflow Summary

Every workflow run includes a summary:
- **Actions** → Select a workflow run → **Summary** tab
- Shows vulnerability counts by severity
- Quick overview without downloading files

### Severity Levels

| SARIF Level | Trivy Severity | Description |
|-------------|----------------|-------------|
| `error` | CRITICAL/HIGH | Critical vulnerabilities requiring immediate attention |
| `warning` | MEDIUM | Moderate vulnerabilities to address soon |
| `note` | LOW/INFO | Low-priority vulnerabilities or informational findings |

## Security Scanning Configuration

### Current Setup

The pipeline scans:
- ✅ **Filesystem**: All repository files and dependencies
- ✅ **Dependencies**: Python packages in `pyproject.toml`
- ✅ **Configuration**: Docker files, CI/CD configs
- ✅ **Secrets**: Potential secret leaks (via Trivy)

### Scan Frequency

Scans run automatically on:
- ✅ Push to `main` or `develop` branches
- ✅ Pull requests to `main`
- ✅ Tag creation (`v*`)

### Customize Scan Configuration

Edit `.github/workflows/ci-cd.yml` to customize:

```yaml
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    scan-type: 'fs'           # Filesystem scan
    scan-ref: '.'             # Scan entire repo
    format: 'sarif'           # Output format
    output: 'trivy-results.sarif'
    severity: 'CRITICAL,HIGH' # Only report high/critical (optional)
    ignore-unfixed: true      # Ignore unfixed vulnerabilities (optional)
```

## Additional Security Features

### 1. Dependabot Alerts

Enable automated dependency updates:

1. **Settings** → **Security & analysis**
2. Enable **Dependabot alerts**
3. Enable **Dependabot security updates**

This will:
- Automatically detect vulnerable dependencies
- Create PRs to update them
- Keep your dependencies up-to-date

### 2. Secret Scanning

Prevent secrets from being committed:

1. **Settings** → **Security & analysis**
2. Enable **Secret scanning**
3. Enable **Push protection** (prevents pushing secrets)

This detects:
- API keys
- Tokens
- Passwords
- Private keys
- Database connection strings

### 3. Branch Protection

Protect main branch from bypassing security checks:

1. **Settings** → **Branches**
2. Add rule for `main` branch
3. Enable:
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - ✅ Require security scan to pass
   - ✅ Require pull request reviews

## Workflow Improvements

### Current Workflow Behavior

The security scan workflow is configured to:

1. **Always run** (`if: always()`) even if previous jobs fail
2. **Continue on error** (`continue-on-error: true`) if Code Scanning upload fails
3. **Upload artifacts** so results are never lost
4. **Display summary** in the workflow run summary

This ensures security scans always complete and results are accessible even if GitHub Code Scanning isn't enabled.

### Making Scans Blocking (Optional)

To fail the workflow if critical vulnerabilities are found:

```yaml
- name: Check for critical vulnerabilities
  run: |
    critical=$(jq '[.runs[].results[] | select(.level == "error")] | length' trivy-results.sarif)
    if [ "$critical" -gt "0" ]; then
      echo "❌ Critical vulnerabilities found!"
      exit 1
    fi
```

Add this step after the Trivy scan to block merges with critical vulnerabilities.

## Troubleshooting

### Error: "Code scanning is not enabled for this repository"

**Solution**: Follow the "Enable GitHub Code Scanning" section above.

**Workaround**: The workflow still succeeds and saves results as artifacts. You can:
- Download the `trivy-results` artifact
- View the summary in the workflow run
- Enable Code Scanning later to see results in Security tab

### Error: "Resource not accessible by integration"

**Causes**:
1. Insufficient permissions (fixed by adding `permissions:` block)
2. Running on a fork (expected behavior)
3. Code Scanning not enabled

**Solution**: Ensure you're not on a fork and Code Scanning is enabled.

### Results Not Showing in Security Tab

1. Verify Code Scanning is enabled: **Settings** → **Security & analysis**
2. Check workflow permissions: Should have `security-events: write`
3. Wait a few minutes - GitHub may take time to process SARIF files
4. Check for errors in workflow logs

### No Vulnerabilities Found (But Expected Some)

1. Check the Trivy scan output in workflow logs
2. Verify scan configuration (severity levels, ignore-unfixed, etc.)
3. Dependencies may actually be up-to-date (good!)

## Best Practices

1. ✅ **Enable all security features** - Code Scanning, Dependabot, Secret Scanning
2. ✅ **Review alerts regularly** - Check Security tab weekly
3. ✅ **Set up notifications** - Get alerts for new vulnerabilities
4. ✅ **Update dependencies** - Merge Dependabot PRs promptly
5. ✅ **Use branch protection** - Require security checks before merging
6. ✅ **Monitor workflow runs** - Ensure scans complete successfully
7. ✅ **Document exceptions** - Use `.trivyignore` for false positives

## Resources

- [GitHub Code Scanning Documentation](https://docs.github.com/en/code-security/code-scanning)
- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [SARIF Format Specification](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security/getting-started/github-security-features)

## Next Steps

1. ✅ **Enable Code Scanning** following this guide
2. ⏳ **Review current vulnerabilities** in Security tab (after enabling)
3. ⏳ **Set up Dependabot** for automated updates
4. ⏳ **Configure branch protection** to require security checks
5. ⏳ **Set up notifications** for security alerts

Once Code Scanning is enabled, your security workflow will be fully functional and vulnerabilities will be displayed directly in the GitHub UI.
