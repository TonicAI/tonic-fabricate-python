# 📦 Publishing the Tonic Fabricate Python Client Library

## ✅ Current Status

Your package is **ready for publication**! The package structure includes:

- Modern `pyproject.toml` configuration
- Legacy `setup.py` for compatibility
- Proper package structure with `fabricate_client/`
- README.md with usage documentation
- MANIFEST.in for including additional files
- Version management (currently v1.0.0)
- Package name: `tonic-fabricate`
- Import name: `fabricate_client`

## 🚀 Publishing Process

You can publish this package in two ways:

1. **Manual Publishing** - Using the command line scripts
2. **Automated Publishing** - Using GitHub Actions (recommended)

### **Option 1: Manual Publishing**

#### **1. Prerequisites**

You'll need accounts on:

- **TestPyPI** (for testing): https://test.pypi.org/account/register/
- **PyPI** (production): https://pypi.org/account/register/

#### **2. Configure API Tokens**

**For TestPyPI:**

1. Go to https://test.pypi.org/manage/account/token/
2. Create a new token with scope "Entire account"
3. Save it securely

**For PyPI:**

1. Go to https://pypi.org/manage/account/token/
2. Create a new token with scope "Entire account"
3. Save it securely

#### **3. Update Version Number (if needed)**

Simply update the version in **one place** - `pyproject.toml`:

```toml
# In pyproject.toml (line 7)
version = "x.y.z"
```

**Quick update command:**

```bash
# Example: Update from 1.0.0 to 1.0.1
sed -i '' 's/version = "1.0.0"/version = "1.0.1"/' pyproject.toml

# Verify the change
grep "version =" pyproject.toml
```

✅ **Single Source of Truth:** The other files (`setup.py` and `__init__.py`) automatically read the version from `pyproject.toml` at build time and runtime using the `tomllib`/`tomli` library.

#### **4. Test Publishing**

```bash
# Navigate to the client directory
cd /Users/mark/Code/fabricate/clients/python

# Run the test publishing script
./publish-test.sh
```

You'll be prompted for:

- **Username**: `__token__`
- **Password**: Your TestPyPI API token (including the `pypi-` prefix)

#### **5. Verify Test Installation**

```bash
# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ tonic-fabricate

# Test the package
python -c "from fabricate_client import generate; print('Package works!')"
```

#### **6. Production Publishing**

⚠️ **Only do this after testing is successful!**

```bash
# Run the production publishing script
./publish.sh
```

The script will:

- Ask for multiple confirmations (this is for safety!)
- Check version validity
- Verify package integrity
- Upload to production PyPI

You'll be prompted for:

- **Username**: `__token__`
- **Password**: Your PyPI API token (including the `pypi-` prefix)

#### **7. Verify Production Installation**

```bash
# Test installation from PyPI
pip install tonic-fabricate

# Test the package
python -c "from fabricate_client import generate; print('Package installed successfully!')"
```

### **Option 2: Automated Publishing with GitHub Actions (Recommended)**

The repository includes a GitHub Actions workflow that automatically publishes to PyPI when you create a release or manually trigger the workflow.

#### **1. Setup GitHub Secrets**

First, you need to configure your PyPI API token as a GitHub secret:

1. **Create a PyPI API token:**

   - Go to https://pypi.org/manage/account/token/
   - Create a new token with scope "Entire account"
   - Copy the token (it starts with `pypi-`)

2. **Add the token to GitHub Secrets:**
   - Go to your repository on GitHub
   - Navigate to **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret**
   - Name: `PYPI_API_TOKEN`
   - Value: Your PyPI API token (including the `pypi-` prefix)

#### **2. Publishing Methods**

**Method A: Automatic on Release (Recommended)**

1. Create a new release on GitHub:

   ```bash
   # Tag the current commit
   git tag v1.0.2
   git push origin v1.0.2
   ```

2. Go to GitHub → **Releases** → **Create a new release**
3. Select the tag you just created
4. Fill in release notes
5. Click **Publish release**

The workflow will automatically trigger and publish to PyPI.

**Method B: Manual Trigger**

1. Go to GitHub → **Actions** → **Publish to PyPI**
2. Click **Run workflow**
3. Type `PUBLISH` in the confirmation field
4. Click **Run workflow**

#### **3. Workflow Features**

The GitHub Actions workflow:

- ✅ Runs the same `publish.sh` script in non-interactive mode
- ✅ Uses secure PyPI token from GitHub secrets
- ✅ Provides detailed logging and error handling
- ✅ Automatically uploads build artifacts to the GitHub release
- ✅ Works with the existing version management system

#### **4. Monitoring the Workflow**

After triggering the workflow:

1. Go to **Actions** tab in your GitHub repository
2. Click on the running workflow to see detailed logs
3. Monitor each step of the publishing process
4. If successful, your package will be available on PyPI within minutes

#### **5. Environment Protection (Optional)**

For additional security, you can set up environment protection:

1. Go to **Settings** → **Environments**
2. Create a `production` environment
3. Add protection rules (e.g., required reviewers)
4. Move the `PYPI_API_TOKEN` secret to this environment

This ensures that publishing requires manual approval even when automated.

## 🔄 Version Management Guidelines

### **Semantic Versioning:**

- **PATCH** (z): Bug fixes (e.g., 1.0.0 → 1.0.1)
- **MINOR** (y): New features, backward compatible (e.g., 1.0.0 → 1.1.0)
- **MAJOR** (x): Breaking changes (e.g., 1.0.0 → 2.0.0)

### **Single Source Management:**

- ✅ **Only edit:** `pyproject.toml`
- ✅ **Automatic sync:** `setup.py` and `__init__.py` read from `pyproject.toml`
- ✅ **No version conflicts:** Impossible for versions to get out of sync
- ✅ **Modern approach:** Uses `tomllib` (Python 3.11+) or `tomli` (Python 3.8-3.10)

## 🎯 Quick Publishing Workflow

### **GitHub Actions (Recommended)**

```bash
# 1. Update version in pyproject.toml (if needed)
# 2. Commit and push changes
git add pyproject.toml
git commit -m "Bump version to x.y.z"
git push

# 3. Create and push tag
git tag vx.y.z
git push origin vx.y.z

# 4. Create GitHub release (triggers automatic publishing)
# Go to GitHub → Releases → Create a new release
```

### **Manual Publishing**

```bash
# 1. Navigate to directory
cd /Users/mark/Code/tonic-fabricate-python

# 2. Update version (if needed)
# Edit only pyproject.toml - other files read it automatically

# 3. Test publish
./publish-test.sh

# 4. Verify test installation
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ tonic-fabricate

# 5. Production publish
./publish.sh
```

## 🚨 Important Notes

1. **Package Name**: Installable as `tonic-fabricate`
2. **Import Name**: Import as `fabricate_client`
3. **Version Update**: Only update version in `pyproject.toml`
4. **GitHub Actions**: Requires `PYPI_API_TOKEN` secret to be configured
5. **Always test first**: Use TestPyPI before production (manual) or test releases (GitHub Actions)
6. **No duplicates**: You cannot upload the same version twice

## 📚 Resources

- [TestPyPI](https://test.pypi.org/)
- [PyPI](https://pypi.org/)
- [Semantic Versioning](https://semver.org/)

## 🔍 Troubleshooting

**"File already exists" error:**

- Increment the version number in `pyproject.toml`

**Authentication errors:**

- Ensure API token includes the `pypi-` prefix
- Username should be `__token__`

**Import errors after installation:**

- Verify package name (`tonic-fabricate`) vs import name (`fabricate_client`)
