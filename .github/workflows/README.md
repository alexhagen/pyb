# GitHub Actions Workflows

This directory contains GitHub Actions workflows for automated testing and publishing.

## Workflows

### test.yml - Continuous Integration

Runs on every push and pull request to main/master/develop branches.

**What it does:**
- Tests the package on multiple OS (Ubuntu, macOS, Windows)
- Tests against Python 3.10, 3.11, and 3.12
- Runs pytest with coverage reporting
- Uploads coverage to Codecov

**Setup required:**
- No secrets needed for basic testing
- Optional: Add `CODECOV_TOKEN` secret for private repos

### publish.yml - PyPI Publishing

Runs when you create a GitHub release or manually trigger it.

**What it does:**
- Builds the package (sdist and wheel)
- Validates the build with `twine check`
- Publishes to PyPI on release
- Can publish to TestPyPI via manual trigger

**Setup required:**

1. **Create PyPI API token:**
   - Go to https://pypi.org/manage/account/token/
   - Create a new API token
   - Copy the token (starts with `pypi-`)

2. **Add token to GitHub secrets:**
   - Go to your repo: Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `PYPI_API_TOKEN`
   - Value: Your PyPI token
   - Click "Add secret"

3. **Optional - TestPyPI token:**
   - Create token at https://test.pypi.org/manage/account/token/
   - Add as `TEST_PYPI_API_TOKEN` secret

## Usage

### Running Tests

Tests run automatically on push/PR. To see results:
- Go to the "Actions" tab in your GitHub repo
- Click on the latest workflow run

### Publishing to PyPI

**Method 1: Create a GitHub Release (Recommended)**
1. Go to your repo → Releases → "Draft a new release"
2. Create a new tag (e.g., `v3.0.0`)
3. Fill in release notes
4. Click "Publish release"
5. The workflow will automatically publish to PyPI

**Method 2: Manual Trigger**
1. Go to Actions → "Publish to PyPI"
2. Click "Run workflow"
3. Choose to publish to TestPyPI or PyPI
4. Click "Run workflow"

## Troubleshooting

### Tests failing
- Check the workflow logs in the Actions tab
- Run tests locally: `pytest`
- Ensure all dependencies are in `pyproject.toml`

### Publishing fails
- Verify `PYPI_API_TOKEN` secret is set correctly
- Check that version number is incremented
- Ensure package builds locally: `python -m build`

### Badge not showing
- Wait a few minutes after first workflow run
- Check badge URL in README.md matches your repo
- Ensure workflow file is named exactly `test.yml`
