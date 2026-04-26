import "./style.css";
import { ScanPDFs, RunMainPy, IsRunning, GetRootInfo, IsSetupDone, PickProjectDir } from "../wailsjs/go/main/App";
import { EventsOn } from "../wailsjs/runtime/runtime";
import { main as appns } from "../wailsjs/go/models";

type PDFItem = appns.PDFItem;

const root = document.querySelector<HTMLDivElement>("#app")!;
root.innerHTML = `
  <div id="setup-overlay" hidden>
    <div class="setup-card">
      <div class="setup-icon">📁</div>
      <h2>初回セットアップ</h2>
      <p>
        <code>webclass_kadai_getter</code> フォルダを選択してください。<br>
        <span class="setup-hint">main.py が含まれているフォルダです。</span>
      </p>
      <button id="pick-dir">フォルダを選択...</button>
      <div class="setup-error" id="setup-error" hidden></div>
    </div>
  </div>
  <div class="topbar">
    <h1>📚 WebClass PDF Viewer</h1>
    <span class="info" id="info"></span>
    <div class="spacer"></div>
    <button class="ghost" id="reload">再読み込み</button>
    <button id="fetch">取得開始</button>
  </div>
  <aside id="sidebar">
    <header>
      <input id="search" type="search" placeholder="検索 (授業/コース/ファイル名)" />
      <div class="stats" id="stats"></div>
    </header>
    <nav id="tree"></nav>
  </aside>
  <main>
    <div class="placeholder" id="placeholder">
      <div>📄</div>
      <div>左のリストからPDFを選択してください</div>
    </div>
    <iframe id="viewer" hidden></iframe>
  </main>
  <section id="log-panel">
    <div class="log-header">
      <span class="title">実行ログ</span>
      <span class="status idle" id="status">待機中</span>
      <div style="flex:1"></div>
      <button class="ghost" id="clear-log">クリア</button>
    </div>
    <div id="log"></div>
  </section>
`;

const setupOverlay = document.querySelector<HTMLDivElement>("#setup-overlay")!;
const pickDirBtn = document.querySelector<HTMLButtonElement>("#pick-dir")!;
const setupError = document.querySelector<HTMLDivElement>("#setup-error")!;
const treeEl = document.querySelector<HTMLElement>("#tree")!;
const searchEl = document.querySelector<HTMLInputElement>("#search")!;
const statsEl = document.querySelector<HTMLDivElement>("#stats")!;
const infoEl = document.querySelector<HTMLSpanElement>("#info")!;
const viewer = document.querySelector<HTMLIFrameElement>("#viewer")!;
const placeholder = document.querySelector<HTMLDivElement>("#placeholder")!;
const fetchBtn = document.querySelector<HTMLButtonElement>("#fetch")!;
const reloadBtn = document.querySelector<HTMLButtonElement>("#reload")!;
const clearLogBtn = document.querySelector<HTMLButtonElement>("#clear-log")!;
const logEl = document.querySelector<HTMLDivElement>("#log")!;
const statusEl = document.querySelector<HTMLSpanElement>("#status")!;

let allItems: PDFItem[] = [];
let activeEl: HTMLElement | null = null;

function fmtSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function fmtDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function escapeHtml(s: string): string {
  return String(s).replace(/[&<>"']/g, (c) => {
    const map: Record<string, string> = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    };
    return map[c];
  });
}

type Tree = Record<string, Record<string, Record<string, PDFItem[]>>>;

function groupItems(items: PDFItem[]): Tree {
  const tree: Tree = {};
  for (const it of items) {
    const cls = it.class || "(未分類)";
    const course = it.course || "(直下)";
    const content = it.content || "(直下)";
    tree[cls] ??= {};
    tree[cls][course] ??= {};
    tree[cls][course][content] ??= [];
    tree[cls][course][content].push(it);
  }
  return tree;
}

function selectPdf(item: PDFItem, el: HTMLElement) {
  if (activeEl) activeEl.classList.remove("active");
  el.classList.add("active");
  activeEl = el;
  placeholder.style.display = "none";
  viewer.hidden = false;
  viewer.src = `/pdfs/${encodeURI(item.path)}`;
}

function render(items: PDFItem[]) {
  treeEl.innerHTML = "";
  if (items.length === 0) {
    treeEl.innerHTML = `<div class="empty">PDFが見つかりませんでした<br><br>「取得開始」ボタンを押して資料をダウンロードしてください</div>`;
    return;
  }
  const grouped = groupItems(items);
  for (const className of Object.keys(grouped).sort()) {
    const courses = grouped[className];
    const totalInClass = Object.values(courses)
      .flatMap((c) => Object.values(c))
      .reduce((a, b) => a + b.length, 0);

    const classDetails = document.createElement("details");
    classDetails.open = true;
    const classSummary = document.createElement("summary");
    classSummary.className = "class-summary";
    classSummary.innerHTML = `<span>📚 ${escapeHtml(className)}</span><span class="count">${totalInClass}</span>`;
    classDetails.appendChild(classSummary);

    for (const courseName of Object.keys(courses).sort()) {
      const contents = courses[courseName];
      const totalInCourse = Object.values(contents).reduce(
        (a, b) => a + b.length,
        0,
      );

      const courseDetails = document.createElement("details");
      courseDetails.open = true;
      const courseSummary = document.createElement("summary");
      courseSummary.className = "course-summary";
      courseSummary.innerHTML = `<span>📂 ${escapeHtml(courseName)}</span><span class="count">${totalInCourse}</span>`;
      courseDetails.appendChild(courseSummary);

      for (const contentName of Object.keys(contents).sort()) {
        const pdfs = contents[contentName];
        const contentDetails = document.createElement("details");
        contentDetails.open = true;
        const contentSummary = document.createElement("summary");
        contentSummary.className = "content-summary";
        contentSummary.innerHTML = `<span>📁 ${escapeHtml(contentName)}</span><span class="count">${pdfs.length}</span>`;
        contentDetails.appendChild(contentSummary);

        for (const pdf of pdfs) {
          const item = document.createElement("div");
          item.className = "pdf-item";
          item.innerHTML = `
            <span>📄</span>
            <span class="pdf-name">${escapeHtml(pdf.filename)}</span>
            <span class="pdf-meta">${fmtSize(pdf.size)} · ${fmtDate(pdf.mtime)}</span>
          `;
          item.addEventListener("click", () => selectPdf(pdf, item));
          contentDetails.appendChild(item);
        }
        courseDetails.appendChild(contentDetails);
      }
      classDetails.appendChild(courseDetails);
    }
    treeEl.appendChild(classDetails);
  }
}

function applyFilter() {
  const q = searchEl.value.trim().toLowerCase();
  if (!q) {
    render(allItems);
    return;
  }
  const filtered = allItems.filter((it) =>
    [it.class, it.course, it.content, it.filename]
      .join("\n")
      .toLowerCase()
      .includes(q),
  );
  render(filtered);
}

async function loadPdfs() {
  try {
    const r = await ScanPDFs();
    allItems = r.items ?? [];
    statsEl.textContent = `${allItems.length} 件のPDF`;
    render(allItems);
  } catch (e: any) {
    treeEl.innerHTML = `<div class="empty">読み込みエラー: ${escapeHtml(e?.message ?? String(e))}</div>`;
  }
}

async function loadInfo() {
  try {
    const info = await GetRootInfo();
    infoEl.textContent = info.classDir;
  } catch {
    /* noop */
  }
}

function classifyLog(line: string): string {
  if (line.startsWith("[ERROR]") || line.includes("✗")) return "error";
  if (line.startsWith("[OK]") || line.startsWith("[DONE]") || line.includes("✓"))
    return "ok";
  if (line.startsWith("[INFO]") || line.startsWith("ℹ")) return "info";
  if (line.startsWith("[EXIT]") || line.includes("!")) return "warn";
  return "";
}

function appendLog(line: string) {
  const div = document.createElement("div");
  div.className = `log-line ${classifyLog(line)}`;
  div.textContent = line;
  logEl.appendChild(div);
  logEl.scrollTop = logEl.scrollHeight;
}

function setRunning(running: boolean) {
  fetchBtn.disabled = running;
  fetchBtn.textContent = running ? "取得中..." : "取得開始";
  statusEl.textContent = running ? "実行中" : "待機中";
  statusEl.className = `status ${running ? "running" : "idle"}`;
}

async function startFetch() {
  if (await IsRunning()) return;
  logEl.innerHTML = "";
  setRunning(true);
  try {
    await RunMainPy();
  } catch (e: any) {
    appendLog(`[ERROR] ${e?.message ?? String(e)}`);
    setRunning(false);
  }
}

async function checkSetup() {
  const done = await IsSetupDone();
  if (!done) {
    setupOverlay.hidden = false;
  }
}

pickDirBtn.addEventListener("click", async () => {
  setupError.hidden = true;
  pickDirBtn.disabled = true;
  pickDirBtn.textContent = "選択中...";
  try {
    const dir = await PickProjectDir();
    if (dir) {
      setupOverlay.hidden = true;
      await loadInfo();
      await loadPdfs();
    }
  } catch (e: any) {
    setupError.textContent = e?.message ?? String(e);
    setupError.hidden = false;
  } finally {
    pickDirBtn.disabled = false;
    pickDirBtn.textContent = "フォルダを選択...";
  }
});

EventsOn("fetch:started", () => setRunning(true));
EventsOn("fetch:log", (line: string) => appendLog(line));
EventsOn("fetch:done", async () => {
  setRunning(false);
  await loadPdfs();
});

fetchBtn.addEventListener("click", startFetch);
reloadBtn.addEventListener("click", loadPdfs);
clearLogBtn.addEventListener("click", () => (logEl.innerHTML = ""));
searchEl.addEventListener("input", applyFilter);

checkSetup();
loadInfo();
loadPdfs();
