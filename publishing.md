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

### **1. Prerequisites**

You'll need accounts on:

- **TestPyPI** (for testing): https://test.pypi.org/account/register/
- **PyPI** (production): https://pypi.org/account/register/

### **2. Configure API Tokens**

**For TestPyPI:**

1. Go to https://test.pypi.org/manage/account/token/
2. Create a new token with scope "Entire account"
3. Save it securely

**For PyPI:**

1. Go to https://pypi.org/manage/account/token/
2. Create a new token with scope "Entire account"
3. Save it securely

### **3. Update Version Number (if needed)**

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

### **4. Test Publishing**

```bash
# Navigate to the client directory
cd /Users/mark/Code/fabricate/clients/python

# Run the test publishing script
./publish-test.sh
```

You'll be prompted for:

- **Username**: `__token__`
- **Password**: Your TestPyPI API token (including the `pypi-` prefix)

### **5. Verify Test Installation**

```bash
# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ tonic-fabricate

# Test the package
python -c "from fabricate_client import generate; print('Package works!')"
```

### **6. Production Publishing**

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

### **7. Verify Production Installation**

```bash
# Test installation from PyPI
pip install tonic-fabricate

# Test the package
python -c "from fabricate_client import generate; print('Package installed successfully!')"
```

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

```bash
# 1. Navigate to directory
cd /Users/mark/Code/fabricate/clients/python

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
4. **Always test first**: Use TestPyPI before production
5. **No duplicates**: You cannot upload the same version twice

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
