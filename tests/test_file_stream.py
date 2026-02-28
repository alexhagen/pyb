"""
Tests for FileStringStream class.
"""

import pytest
from pyb.pyb import FileStringStream


class TestFileStringStream:
    """Test FileStringStream functionality."""
    
    def test_init(self):
        """Test FileStringStream initialization."""
        stream = FileStringStream()
        assert stream.file_string == ""
        assert str(stream) == ""
    
    def test_add_line_single(self):
        """Test adding a single line."""
        stream = FileStringStream()
        stream.add_line("import bpy")
        assert str(stream) == "import bpy\n"
    
    def test_add_line_multiple(self):
        """Test adding multiple lines."""
        stream = FileStringStream()
        stream.add_line("import bpy")
        stream.add_line("import math")
        assert str(stream) == "import bpy\nimport math\n"
    
    def test_add_line_with_newline(self):
        """Test that add_line handles strings with newlines."""
        stream = FileStringStream()
        stream.add_line("line1\nline2")
        assert str(stream) == "line1\nline2\n"
    
    def test_a_method_alias(self):
        """Test that 'a' method is an alias for add_line."""
        stream = FileStringStream()
        stream.a("test line")
        assert str(stream) == "test line\n"
    
    def test_a_method_with_args(self):
        """Test 'a' method with string formatting."""
        stream = FileStringStream()
        stream.a("value: 42 end")
        assert "value:" in str(stream)
        assert "42" in str(stream)
        assert "end" in str(stream)
    
    def test_copy(self):
        """Test copying a FileStringStream."""
        stream1 = FileStringStream()
        stream1.add_line("line 1")
        stream1.add_line("line 2")
        
        stream2 = stream1.copy()
        assert str(stream1) == str(stream2)
        
        # Verify they are independent
        stream2.add_line("line 3")
        assert "line 3" in str(stream2)
        assert "line 3" not in str(stream1)
    
    def test_empty_string(self):
        """Test empty FileStringStream."""
        stream = FileStringStream()
        assert str(stream) == ""
        assert len(str(stream)) == 0
    
    def test_chaining(self):
        """Test method chaining if supported."""
        stream = FileStringStream()
        stream.add_line("line 1")
        stream.add_line("line 2")
        stream.add_line("line 3")
        
        result = str(stream)
        assert result.count("\n") == 3
        assert "line 1" in result
        assert "line 2" in result
        assert "line 3" in result
    
    def test_special_characters(self):
        """Test handling of special characters."""
        stream = FileStringStream()
        stream.add_line("# Comment with special chars: @#$%^&*()")
        stream.add_line('string = "quoted text"')
        stream.add_line("path = '/usr/bin/blender'")
        
        result = str(stream)
        assert "@#$%^&*()" in result
        assert '"quoted text"' in result
        assert "'/usr/bin/blender'" in result
    
    def test_unicode(self):
        """Test handling of unicode characters."""
        stream = FileStringStream()
        stream.add_line("# Unicode: α β γ δ ε")
        stream.add_line("# Emoji: 🎨 🖼️ 🎭")
        
        result = str(stream)
        assert "α β γ δ ε" in result
        assert "🎨" in result
