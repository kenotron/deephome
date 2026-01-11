
from pathlib import Path
from deepagents.backends import FilesystemBackend
import asyncio
import inspect

async def test_fs_write():
    root = Path("./test_fs_workspace")
    root.mkdir(exist_ok=True)
    backend = FilesystemBackend(root_dir=root)
    
    print(f"Backend attributes: {dir(backend)}")
    
    # Check for likely names
    for name in ['write_file', 'write', 'save_file', 'save']:
        if hasattr(backend, name):
            print(f"Found method: {name}")
            print(inspect.signature(getattr(backend, name)))

if __name__ == "__main__":
    asyncio.run(test_fs_write())
