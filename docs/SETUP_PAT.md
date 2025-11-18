# Setup Personal Access Token for Cross-Repository Dispatch

To enable automatic version updates in the `homeassistant-addons` repository, you need to create a Personal Access Token (PAT) with the appropriate permissions.

## Steps to Create PAT

### 1. Create Personal Access Token

1. Go to [GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens)
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Configure the token:
   - **Note**: `CI/CD Cross-Repo Dispatch`
   - **Expiration**: Choose your preferred expiration (recommend 90 days or 1 year)
   - **Scopes**: Select the following:
     - ✅ `repo` (Full control of private repositories)
       - This includes `repo:status`, `repo_deployment`, `public_repo`, etc.
     - ✅ `workflow` (Update GitHub Action workflows)

4. Click **"Generate token"**
5. **Important**: Copy the token immediately (you won't be able to see it again!)

### 2. Add Token to Repository Secrets

1. Go to [trash_tracking repository settings](https://github.com/iml885203/trash_tracking/settings/secrets/actions)
2. Click **"New repository secret"**
3. Configure the secret:
   - **Name**: `PAT_TOKEN` (must be exactly this name)
   - **Secret**: Paste the token you copied
4. Click **"Add secret"**

### 3. Verify Setup

After adding the secret, the next push to `master` branch will automatically:
1. Run tests
2. Build Docker images
3. Trigger the `homeassistant-addons` repository to update its version

You can verify this by:
1. Pushing a commit to master
2. Check [Actions tab](https://github.com/iml885203/trash_tracking/actions)
3. Look for the "Trigger addon repository update" step - it should succeed
4. Check [homeassistant-addons Actions](https://github.com/iml885203/homeassistant-addons/actions) to see if the version update workflow was triggered

## Security Notes

- ⚠️ **Never commit the PAT to the repository**
- ✅ Store it only in GitHub Secrets
- 🔄 Rotate the token periodically (when it expires or if compromised)
- 🔒 The token has access to all your repositories, so keep it secure

## Alternative: Use GitHub App (Advanced)

For better security, you can create a GitHub App instead of using a PAT:
- [GitHub Apps Documentation](https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/about-creating-github-apps)
- Benefits: Fine-grained permissions, better audit logging, no user association

## Troubleshooting

### Error: "Resource not accessible by integration"
- This means the `GITHUB_TOKEN` was used instead of `PAT_TOKEN`
- Verify the secret is named exactly `PAT_TOKEN`
- Check that the workflow uses `${{ secrets.PAT_TOKEN }}`

### Workflow doesn't trigger in homeassistant-addons
- Verify the workflow file exists at `.github/workflows/update-version.yml`
- Check that the `repository_dispatch` event type matches (`version-update`)
- Ensure the PAT has the `workflow` scope enabled
