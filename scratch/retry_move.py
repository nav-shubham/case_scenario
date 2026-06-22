import os
import shutil
import time

src_dir = "inter case scanario"
dst_dir = "data/intermediate"

for folder in ["Original", "Answers", "Pure Question Bank"]:
    src = os.path.join(src_dir, folder)
    dst = os.path.join(dst_dir, folder)
    if os.path.exists(src):
        print(f"Moving {src} -> {dst}")
        # Try moving. If fails, try copying and then deleting
        try:
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.move(src, dst)
            print(f"Successfully moved {folder}")
        except Exception as e:
            print(f"Failed to move {folder}: {e}. Trying copy-and-delete...")
            try:
                shutil.copytree(src, dst, dirs_exist_ok=True)
                # Now try to delete src
                time.sleep(1)
                try:
                    shutil.rmtree(src)
                    print(f"Successfully copied and deleted original {folder}")
                except Exception as del_err:
                    print(f"Copied {folder} but could not delete source: {del_err}")
            except Exception as copy_err:
                print(f"Failed copy-and-delete for {folder}: {copy_err}")

# Try to remove top-level folder if empty
try:
    if os.path.exists(src_dir) and not os.listdir(src_dir):
        os.rmdir(src_dir)
        print("Removed empty source folder 'inter case scanario'")
except Exception as e:
    print(f"Could not remove source folder: {e}")
