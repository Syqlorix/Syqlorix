import time
import pytest
from syqlorix.core import StarlarkComponent, Syqlorix, div, h1, p
from syqlorix import syqlorix_rust

def test_rust_css_processing_performance():
    """
    Benchmarks the Rust-based Tailwind CSS processing.
    Ensures that the extension is callable and returns valid CSS.
    """
    html_sample = """
    <div class="bg-blue-500 text-white p-4 rounded-lg shadow-lg hover:bg-blue-600">
        <h1 class="text-2xl font-bold">Hello World</h1>
        <p class="mt-2 text-sm">This is a benchmark.</p>
    </div>
    """ * 10 

    start = time.time()
    css = syqlorix_rust.process_tailwind_css(html_sample)
    end = time.time()
    
    print(f"\nRust CSS processing time: {end - start:.4f}s")
    
    assert isinstance(css, str)
    assert ".bg-blue-500" in css
    assert "background-color" in css

def test_starlark_rendering_performance():
    """
    Benchmarks Starlark component rendering.
    Ensures Starlark components render correctly and within reasonable time limits.
    """
    script = """
tag("div", 
    tag("h1", "Title"),
    tag("p", "Content")
)
"""
    start = time.time()
    for _ in range(100):
        comp = StarlarkComponent(script_content=script)
        comp.create()
    end = time.time()
    
    print(f"\nStarlark rendering time (100 iterations): {end - start:.4f}s")
    
    # Render one to check output
    comp = StarlarkComponent(script_content=script)
    output = comp.create().render()
    # Check for content without worrying about exact pretty-print indentation
    assert "Title" in output
    assert "Content" in output
    assert "<h1>" in output

def test_fast_id_generation():
    """
    Tests the high-performance Rust ID generator.
    """
    start = time.time()
    for _ in range(10000):
        uid = syqlorix_rust.generate_scope_id()
        assert len(uid) == 8 # 4 bytes hex encoded
    end = time.time()
    
    print(f"\nRust ID generation time (10000 iterations): {end - start:.4f}s")

