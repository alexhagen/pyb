# pyb Test Suite

Comprehensive test suite for the pyb (Python Blender) package with 50%+ code coverage.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_file_stream.py      # FileStringStream class tests
├── test_blender_detection.py # Blender detection and execution tests
├── test_pyb_core.py         # Core pyb class functionality tests
├── test_materials.py        # Material and geometry class tests
├── test_mcp_server.py       # MCP server functionality tests
├── test_integration.py      # Integration tests with Docker
└── README.md                # This file
```

## Running Tests

### Run All Tests

```bash
# Run all tests with coverage
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=pyb --cov-report=html --cov-report=term
```

### Run Specific Test Categories

```bash
# Run only unit tests (fast, no Docker needed)
pytest -m "not integration and not docker"

# Run only integration tests (requires Docker)
pytest -m integration

# Run only Docker tests
pytest -m docker

# Skip slow tests
pytest -m "not slow"
```

### Run Specific Test Files

```bash
# Run specific test file
pytest tests/test_pyb_core.py

# Run specific test class
pytest tests/test_pyb_core.py::TestPybPrimitives

# Run specific test
pytest tests/test_pyb_core.py::TestPybPrimitives::test_sphere
```

## Test Categories

### Unit Tests (Fast)
These tests run without actual Blender execution using mocks:

- **test_file_stream.py**: Tests FileStringStream string building
- **test_blender_detection.py**: Tests Blender detection logic
- **test_pyb_core.py**: Tests script generation for primitives, materials, lights
- **test_materials.py**: Tests material and geometry classes
- **test_mcp_server.py**: Tests MCP server functions

### Integration Tests (Slower)
These tests may execute actual Blender rendering:

- **test_integration.py**: End-to-end rendering tests with Docker

## Coverage Goals

The test suite targets **50%+ code coverage** with focus on:

- ✅ **blender_detection.py**: 70%+ coverage
- ✅ **pyb.py**: 60%+ coverage (core functionality)
- ✅ **__init__.py**: 80%+ coverage
- ✅ **mcp_server.py**: 50%+ coverage
- ✅ **blender_geo.py**: 40%+ coverage
- ✅ **blender_matl.py**: 40%+ coverage

## Viewing Coverage Reports

After running tests with coverage:

```bash
# View HTML coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows

# View terminal coverage report
pytest --cov=pyb --cov-report=term-missing
```

## Test Fixtures

Key fixtures available in `conftest.py`:

- `temp_dir`: Temporary directory for test files
- `mock_blender_executor`: Mock BlenderExecutor to avoid actual execution
- `mock_blender_executor_docker`: Mock Docker-based executor
- `mock_mcp_scenes`: Mock MCP server scene storage
- `skip_if_no_docker`: Skip test if Docker not available
- `has_docker`: Check if Docker is available

## Writing New Tests

### Example Unit Test

```python
def test_new_feature(mock_blender_executor):
    """Test new feature without actual Blender execution."""
    from pyb import pyb
    
    scene = pyb(default_light=False)
    scene.new_feature()
    
    script = str(scene)
    assert "expected_output" in script
```

### Example Integration Test

```python
@pytest.mark.integration
@pytest.mark.docker
def test_new_render(skip_if_no_docker):
    """Test actual rendering with Docker."""
    from pyb import pyb
    
    with tempfile.TemporaryDirectory() as tmpdir:
        scene = pyb(default_light=False)
        scene.sph(c=[0, 0, 0], r=1.0, name="sphere")
        
        output_file = os.path.join(tmpdir, "test.png")
        scene.run(filename=output_file, samples=10)
        
        assert os.path.exists(output_file)
```

## Continuous Integration

The test suite is designed to run in CI/CD environments:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -e .[dev]
    pytest --cov=pyb --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Troubleshooting

### Tests Fail Due to Missing Docker

If Docker tests fail:
```bash
# Skip Docker tests
pytest -m "not docker"
```

### Coverage Below Threshold

If coverage is below 50%:
```bash
# See which lines are not covered
pytest --cov=pyb --cov-report=term-missing

# View detailed HTML report
pytest --cov=pyb --cov-report=html
open htmlcov/index.html
```

### Import Errors

Ensure pyb is installed in development mode:
```bash
pip install -e .
# or with dev dependencies
pip install -e .[dev]
```

## Test Markers

Available pytest markers:

- `@pytest.mark.slow`: Marks slow tests
- `@pytest.mark.docker`: Requires Docker
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.requires_blender`: Requires local Blender installation

## Contributing

When adding new features:

1. Write unit tests first (TDD approach)
2. Ensure tests pass: `pytest`
3. Check coverage: `pytest --cov=pyb`
4. Add integration tests if needed
5. Update this README if adding new test categories

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [pyb documentation](https://alexhagen.github.io/pyb)
