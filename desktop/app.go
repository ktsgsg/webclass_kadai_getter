package main

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/wailsapp/wails/v2/pkg/runtime"
)

var ansiRe = regexp.MustCompile(`\x1b(\[[0-?]*[ -/]*[@-~]|\][^\x07]*(\x07|\x1b\\)|[@-_])`)

func cleanLogLine(s string) string {
	s = ansiRe.ReplaceAllString(s, "")
	if idx := strings.LastIndex(s, "\r"); idx >= 0 {
		s = s[idx+1:]
	}
	return strings.TrimRight(s, " \t")
}

type appConfig struct {
	RootDir string `json:"rootDir"`
}

func configFilePath() string {
	dir, err := os.UserConfigDir()
	if err != nil {
		dir, _ = os.UserHomeDir()
	}
	return filepath.Join(dir, "webclass-viewer", "config.json")
}

func loadAppConfig() *appConfig {
	data, err := os.ReadFile(configFilePath())
	if err != nil {
		return &appConfig{}
	}
	var cfg appConfig
	if err := json.Unmarshal(data, &cfg); err != nil {
		return &appConfig{}
	}
	return &cfg
}

func (a *App) saveAppConfig() error {
	p := configFilePath()
	if err := os.MkdirAll(filepath.Dir(p), 0755); err != nil {
		return err
	}
	data, err := json.Marshal(&appConfig{RootDir: a.rootDir})
	if err != nil {
		return err
	}
	return os.WriteFile(p, data, 0644)
}

type App struct {
	ctx      context.Context
	classDir string
	rootDir  string
	mu       sync.Mutex
	running  bool
}

func NewApp() *App {
	root := ""
	if cfg := loadAppConfig(); cfg.RootDir != "" {
		if _, err := os.Stat(filepath.Join(cfg.RootDir, "main.py")); err == nil {
			root = cfg.RootDir
		}
	}
	if root == "" {
		root = findProjectRoot()
	}
	classDir := filepath.Join(root, "class")
	if env := os.Getenv("WEBCLASS_CLASS_DIR"); env != "" {
		classDir = env
	}
	return &App{
		rootDir:  root,
		classDir: classDir,
	}
}

func findProjectRoot() string {
	if found := walkUpForMainPy(currentDir()); found != "" {
		return found
	}
	if exe, err := os.Executable(); err == nil {
		if resolved, err := filepath.EvalSymlinks(exe); err == nil {
			exe = resolved
		}
		if found := walkUpForMainPy(filepath.Dir(exe)); found != "" {
			return found
		}
	}
	if home, err := os.UserHomeDir(); err == nil {
		guess := filepath.Join(home, "Documents", "GitHub", "webclass_worksgetter", "webclass_kadai_getter")
		if _, err := os.Stat(filepath.Join(guess, "main.py")); err == nil {
			return guess
		}
	}
	return currentDir()
}

func currentDir() string {
	if cwd, err := os.Getwd(); err == nil {
		return cwd
	}
	return "."
}

func walkUpForMainPy(start string) string {
	dir := start
	for i := 0; i < 12; i++ {
		if _, err := os.Stat(filepath.Join(dir, "main.py")); err == nil {
			return dir
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			break
		}
		dir = parent
	}
	return ""
}

func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
}

func (a *App) IsSetupDone() bool {
	_, err := os.Stat(filepath.Join(a.rootDir, "main.py"))
	return err == nil
}

func (a *App) PickProjectDir() (string, error) {
	dir, err := runtime.OpenDirectoryDialog(a.ctx, runtime.OpenDialogOptions{
		Title: "webclass_kadai_getter フォルダを選択してください",
	})
	if err != nil {
		return "", err
	}
	if dir == "" {
		return "", nil
	}
	if _, err := os.Stat(filepath.Join(dir, "main.py")); err != nil {
		return "", fmt.Errorf("選択したフォルダに main.py が見つかりません")
	}
	a.rootDir = dir
	a.classDir = filepath.Join(dir, "class")
	if err := a.saveAppConfig(); err != nil {
		return "", fmt.Errorf("設定の保存に失敗しました: %v", err)
	}
	return dir, nil
}

type PDFItem struct {
	Class    string `json:"class"`
	Course   string `json:"course"`
	Content  string `json:"content"`
	Filename string `json:"filename"`
	Path     string `json:"path"`
	Size     int64  `json:"size"`
	Mtime    string `json:"mtime"`
}

type ScanResult struct {
	Root  string    `json:"root"`
	Items []PDFItem `json:"items"`
}

func (a *App) ScanPDFs() ScanResult {
	result := ScanResult{Root: a.classDir, Items: []PDFItem{}}
	if _, err := os.Stat(a.classDir); err != nil {
		return result
	}
	_ = filepath.Walk(a.classDir, func(p string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() {
			return nil
		}
		if !strings.EqualFold(filepath.Ext(p), ".pdf") {
			return nil
		}
		rel, _ := filepath.Rel(a.classDir, p)
		parts := strings.Split(filepath.ToSlash(rel), "/")
		if len(parts) < 2 {
			return nil
		}
		item := PDFItem{
			Filename: filepath.Base(p),
			Path:     filepath.ToSlash(rel),
			Size:     info.Size(),
			Mtime:    info.ModTime().Format(time.RFC3339),
		}
		item.Class = parts[0]
		if len(parts) >= 3 {
			item.Course = parts[1]
		}
		if len(parts) >= 4 {
			item.Content = parts[2]
		}
		result.Items = append(result.Items, item)
		return nil
	})
	sort.Slice(result.Items, func(i, j int) bool {
		x, y := result.Items[i], result.Items[j]
		if x.Class != y.Class {
			return x.Class < y.Class
		}
		if x.Course != y.Course {
			return x.Course < y.Course
		}
		if x.Content != y.Content {
			return x.Content < y.Content
		}
		return x.Filename < y.Filename
	})
	return result
}

func (a *App) GetRootInfo() map[string]string {
	return map[string]string{
		"root":     a.rootDir,
		"classDir": a.classDir,
	}
}

func (a *App) IsRunning() bool {
	a.mu.Lock()
	defer a.mu.Unlock()
	return a.running
}

func (a *App) RunMainPy() error {
	a.mu.Lock()
	if a.running {
		a.mu.Unlock()
		return fmt.Errorf("既に実行中です")
	}
	a.running = true
	a.mu.Unlock()

	go func() {
		defer func() {
			a.mu.Lock()
			a.running = false
			a.mu.Unlock()
			runtime.EventsEmit(a.ctx, "fetch:done")
		}()
		runtime.EventsEmit(a.ctx, "fetch:started")
		runtime.EventsEmit(a.ctx, "fetch:log", fmt.Sprintf("[INFO] working dir: %s", a.rootDir))

		bin, args := resolvePythonCmd(a.rootDir)
		runtime.EventsEmit(a.ctx, "fetch:log", fmt.Sprintf("[INFO] command: %s %s", bin, strings.Join(args, " ")))

		cmd := exec.Command(bin, args...)
		cmd.Dir = a.rootDir
		cmd.Env = append(os.Environ(),
			"PYTHONUNBUFFERED=1",
			"PYTHONIOENCODING=utf-8",
			"NO_COLOR=1",
			"TERM=dumb",
			"FORCE_COLOR=0",
			"COLUMNS=120",
		)
		stdout, err := cmd.StdoutPipe()
		if err != nil {
			runtime.EventsEmit(a.ctx, "fetch:log", fmt.Sprintf("[ERROR] %v", err))
			return
		}
		stderr, err := cmd.StderrPipe()
		if err != nil {
			runtime.EventsEmit(a.ctx, "fetch:log", fmt.Sprintf("[ERROR] %v", err))
			return
		}
		if err := cmd.Start(); err != nil {
			runtime.EventsEmit(a.ctx, "fetch:log", fmt.Sprintf("[ERROR] failed to start: %v", err))
			return
		}
		var wg sync.WaitGroup
		wg.Add(2)
		go streamPipe(a.ctx, stdout, &wg)
		go streamPipe(a.ctx, stderr, &wg)
		wg.Wait()
		if err := cmd.Wait(); err != nil {
			runtime.EventsEmit(a.ctx, "fetch:log", fmt.Sprintf("[EXIT] %v", err))
		} else {
			runtime.EventsEmit(a.ctx, "fetch:log", "[DONE] 取得完了")
		}
	}()
	return nil
}

func resolvePythonCmd(root string) (string, []string) {
	if uv, err := exec.LookPath("uv"); err == nil {
		if _, err := os.Stat(filepath.Join(root, "pyproject.toml")); err == nil {
			return uv, []string{"run", "main.py"}
		}
	}
	venvPython := filepath.Join(root, ".venv", "bin", "python")
	if _, err := os.Stat(venvPython); err == nil {
		return venvPython, []string{"main.py"}
	}
	if py, err := exec.LookPath("python3"); err == nil {
		return py, []string{"main.py"}
	}
	return "python", []string{"main.py"}
}

func streamPipe(ctx context.Context, r io.ReadCloser, wg *sync.WaitGroup) {
	defer wg.Done()
	scanner := bufio.NewScanner(r)
	scanner.Buffer(make([]byte, 0, 64*1024), 1024*1024)
	for scanner.Scan() {
		line := cleanLogLine(scanner.Text())
		if line == "" {
			continue
		}
		runtime.EventsEmit(ctx, "fetch:log", line)
	}
}
