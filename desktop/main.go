package main

import (
	"embed"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"github.com/wailsapp/wails/v2"
	"github.com/wailsapp/wails/v2/pkg/options"
	"github.com/wailsapp/wails/v2/pkg/options/assetserver"
)

//go:embed all:frontend/dist
var assets embed.FS

func main() {
	app := NewApp()

	pdfHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if !strings.HasPrefix(r.URL.Path, "/pdfs/") {
			http.NotFound(w, r)
			return
		}
		rel := strings.TrimPrefix(r.URL.Path, "/pdfs/")
		full := filepath.Join(app.classDir, rel)
		clean, err := filepath.Abs(full)
		if err != nil {
			http.Error(w, "bad path", http.StatusBadRequest)
			return
		}
		base, _ := filepath.Abs(app.classDir)
		if !strings.HasPrefix(clean, base+string(os.PathSeparator)) && clean != base {
			http.Error(w, "forbidden", http.StatusForbidden)
			return
		}
		if !strings.EqualFold(filepath.Ext(clean), ".pdf") {
			http.NotFound(w, r)
			return
		}
		w.Header().Set("Content-Type", "application/pdf")
		http.ServeFile(w, r, clean)
	})

	err := wails.Run(&options.App{
		Title:  "WebClass PDF Viewer",
		Width:  1280,
		Height: 820,
		AssetServer: &assetserver.Options{
			Assets:  assets,
			Handler: pdfHandler,
		},
		BackgroundColour: &options.RGBA{R: 15, G: 23, B: 42, A: 1},
		OnStartup:        app.startup,
		Bind: []interface{}{
			app,
		},
	})

	if err != nil {
		println("Error:", err.Error())
	}
}
