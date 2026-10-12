import sys
from pathlib import Path

def apply_modifications():
    print("Applying download prompt modifications...")

    # Root directory path handling (works cross-platform and handles nested folders)
    base_dir = Path(".")
    
    # Check if files are directly under root or inside desktop-app-2.0.17 subfolder
    if not (base_dir / "js").exists() and (base_dir / "desktop-app-2.0.17" / "js").exists():
        base_dir = base_dir / "desktop-app-2.0.17"

    download_utils_path = base_dir / "js" / "download-utils.ts"
    downloads_path = base_dir / "js" / "downloads.js"

    # 1. Update download-utils.ts
    if download_utils_path.exists():
        content = download_utils_path.read_text(encoding="utf-8")

        if "@tauri-apps/plugin-dialog" not in content:
            content = "import { save, open } from '@tauri-apps/plugin-dialog';\n" + content

        helper_code = """
export async function getCustomSavePath(defaultFilename: string): Promise<string | null> {
  try {
    const filePath = await save({
      title: 'Select Download Location',
      defaultPath: defaultFilename,
    });
    return filePath;
  } catch (e) {
    console.error('Error selecting file path:', e);
    return null;
  }
}

export async function getCustomFolder(): Promise<string | null> {
  try {
    const folderPath = await open({
      directory: true,
      multiple: false,
      title: 'Select Folder for Bulk Downloads',
    });
    return folderPath ? (Array.isArray(folderPath) ? folderPath[0] : folderPath) : null;
  } catch (e) {
    console.error('Error selecting folder:', e);
    return null;
  }
}
"""
        download_utils_path.write_text(content + "\n" + helper_code, encoding="utf-8")
        print(f"Successfully updated: {download_utils_path}")
    else:
        print(f"Could not locate: {download_utils_path}")

    # 2. Update downloads.js
    if downloads_path.exists():
        content = downloads_path.read_text(encoding="utf-8")

        wrapper_code = """
// Interceptor to always ask for download directory/file location
if (typeof window !== 'undefined') {
  window.__getDownloadPathPrompt = async function(defaultName, isBulk = false) {
    try {
      const { save, open } = await import('@tauri-apps/plugin-dialog');
      if (isBulk) {
        const folder = await open({
          directory: true,
          multiple: false,
          title: 'Choose Destination Folder for Bulk Download'
        });
        return folder ? (Array.isArray(folder) ? folder[0] : folder) : null;
      } else {
        const filePath = await save({
          title: 'Save Audio File',
          defaultPath: defaultName
        });
        return filePath || null;
      }
    } catch (err) {
      console.warn('Dialog closed or unavailable:', err);
      return null;
    }
  };
}
"""
        downloads_path.write_text(content + "\n" + wrapper_code, encoding="utf-8")
        print(f"Successfully updated: {downloads_path}")
    else:
        print(f"Could not locate: {downloads_path}")

    print("\nCode modifications complete!")

if __name__ == "__main__":
    apply_modifications()