# 📚 期刊搜索系統 (Journal Search System)

本專案為一個基於 [FastAPI](https://fastapi.tiangolo.com/) 的期刊資訊搜尋與上傳平台，用於搜尋、瀏覽及管理期刊資料，支援繁體中文、英文與葡萄牙文等多語系介面。主要功能包括：

- 🔍 關鍵字搜尋與高級檢索
- 📄 分頁展示期刊結果，支持“無結果”提示
- 🗂 上傳 Excel 資料，含欄位校驗與錯誤提示
- 🌐 三語言切換（繁中 / 英 / 葡）

---

## 📦 安裝指南 (Installation Guide)

### 1️⃣ 安裝 64 位 Python 3.13.2

請從官方下載頁面安裝 Python（請務必選擇 64 位）：

👉 [下載 Python 3.13.2 (64-bit)](https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe)

✅ 勾選安裝選項：
- **Add Python to PATH**
- 安裝 pip（預設勾選）

---

### 2️⃣ 克隆專案並安裝依賴

打開命令提示字元 (CMD)，執行以下命令：

```bash
git clone https://github.com/Mechanic-Hwang/fastApiProject1.git
cd fastApiProject1
pip install -r requirements.txt
```

---

### 3️⃣ 啟動 FastAPI 專案

執行以下指令啟動本地伺服器（假設入口檔為 `main.py` 且有 `app` 變數）：

```bash
uvicorn main:app --reload
```

若主程式位於子資料夾中，請調整路徑，例如：

```bash
uvicorn app.main:app --reload
```

---

## 🌐 使用方式 (Usage)

啟動後，您可以透過以下連結進行存取：

- 預設首頁：`http://127.0.0.1:8000`
---

## 📁 功能簡介 (Features)

### 🔍 搜尋功能

- 支援標題、作者、關鍵詞等欄位搜尋
- 支援高級檢索（多欄位組合查詢）
- 搜尋不到結果會顯示提示訊息

### 📤 資料上傳

- 上傳 Excel 格式期刊資料（單 Sheet）
- 自動識別日期格式錯誤與缺漏欄位
- 檢查重複標題並記錄上傳結果

### 🌍 多語言介面

- 提供繁體中文、英文與葡萄牙文介面
- UI 具語言切換按鈕（地球圖示）

---

## 🗃 資料庫結構 (Database)

- `journals`：儲存期刊主資料
- `upload_logs`：記錄每次上傳的詳細結果與錯誤原因

## 🚀 FastAPI Windows 部署腳本

此腳本會完成以下操作：
1. 安裝 Git（如未安裝）
2. 安裝 Python 3.13（如未安裝）
3. 克隆 Git 倉庫
4. 安裝虛擬環境與依賴
5. 啟動 FastAPI 應用

### 使用方式（需以系統管理員身份執行 PowerShell）：

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
.\deploy-fastapi.ps1
```


---

## 🤝 貢獻方式 (Contributing)

歡迎提交 issue 或 pull request 改進本專案！若您有新功能需求或發現錯誤，請直接提出。

---

## 📜 授權條款 (License)

本專案採用 MIT License。詳見 [LICENSE](./LICENSE)。

---

## 👨‍💻 開發者 (Author)

- GitHub: [Mechanic-Hwang](https://github.com/Mechanic-Hwang)
