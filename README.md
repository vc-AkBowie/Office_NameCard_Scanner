# 📇 ScanVcontact

An AI-driven automated tool designed to streamline business card processing, data extraction, and contact management.

## ✨ Features

* ✂️ **Auto Crop & Merge**: Automatically crops business card images and merges front and back sides side-by-side.
* 🤖 **AI Data Extraction**: Uses Gemini AI to accurately extract contact information (Name, Title, Phone, Email, Company, Address).
* ⚡ **Auto Entry & Structuring**: Parses extracted data without manual entry.
* 📇 **VCF Export**: Automatically generates standard `.vcf` files for seamless import into Microsoft Outlook and smartphones.

---

## 📦 Directory Structure

```diff
📁 ScanVcontact.zip
└── 📁 ScanVcontact/
+   ├── 📦 ScanVcontact.exe          (Main Executable)
+   ├── 📂 _internal/                (System Dependencies)
────────────────────────────────────────────────────────────
    ├── 🔑 api_key.txt               (Gemini API Key)
    ├── 📁 front/                    (All front Card Images)
    ├── 📁 back/                     (All Back Card Images)
    ├── 🖼️ front.(jpg/png)           (Scanned Front Card Image)
    ├── 🖼️ back.(jpg/png)            (Scanned Back Card Image)
    ├── 📁 combined/                 (Merged Output Images)
    └── 📁 vcards_for_outlook/       (Generated VCF Files)
```
