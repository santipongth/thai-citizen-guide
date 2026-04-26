package main

import (
	"bytes"
	"context"
	"io"
	"log/slog"
	"net/http"
	"os"
	"regexp"
	"strings"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

func init() {
	slog.SetLogLoggerLevel(slog.LevelDebug)
}

func main() {
	ctx := context.Background()
	dsn := os.Getenv("DATABASE_URL")

	slog.Info("Connecting to PostgreSQL database")
	pool := mustPanic(pgxpool.New(ctx, dsn))

	proxyHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() { _ = r.Body.Close() }()
		var body bytes.Buffer

		if r.Body != nil {
			_, _ = io.Copy(&body, r.Body)
			r.Body = io.NopCloser(&body)
		}

		slog.Debug("Received HTTP request", "method", r.Method, "path", r.URL.Path, "headers", r.Header, "body", body.String())

		agentID := regexp.MustCompile(`^/agent-proxy/([^/]+)`).FindStringSubmatch(r.URL.Path)
		if len(agentID) < 2 {
			http.Error(w, "Bad Request: missing id", http.StatusBadRequest)
			return
		}

		if !regexp.MustCompile(`^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$`).MatchString(agentID[1]) {
			http.Error(w, "Bad Request: invalid id format", http.StatusBadRequest)
			return
		}

		q := "select endpoint_url, api_headers from agencies where id = $1 and status = 'active'"
		var endpointURL string
		var apiHeaders []map[string]string
		err := pool.QueryRow(ctx, q, agentID[1]).Scan(&endpointURL, &apiHeaders)
		if err == pgx.ErrNoRows {
			http.Error(w, "Not Found", http.StatusNotFound)
			return
		}
		if err != nil {
			slog.Error("Error querying database", slog.Any("error", err))
			http.Error(w, "Internal Server Error", http.StatusInternalServerError)
			return
		}

		req, _ := http.NewRequestWithContext(ctx, r.Method, endpointURL, r.Body)
		req.Header = r.Header.Clone()

		for _, header := range apiHeaders {
			req.Header.Add(header["name"], header["value"])
		}

		for k := range req.Header {
			if strings.HasPrefix(k, "X-Forwarded") {
				req.Header.Del(k)
			}
		}

		resp, err := http.DefaultClient.Do(req)
		if err != nil {
			slog.Error("Error forwarding request to backend", slog.Any("error", err))
			http.Error(w, "Bad Gateway", http.StatusBadGateway)
			return
		}

		defer func() { _ = resp.Body.Close() }()

		for k, v := range resp.Header {
			w.Header()[k] = v
		}

		w.WriteHeader(resp.StatusCode)

		_, err = io.Copy(w, resp.Body)
		if err != nil {
			slog.Error("Error copying response body", slog.Any("error", err))
		}

		q = "update agencies set total_calls = total_calls + 1 where id = $1"
		_, err = pool.Exec(ctx, q, agentID[1])
		if err != nil {
			slog.Error("Error updating total_calls", slog.Any("error", err))
		}
	})

	slog.Info("Starting HTTP server on http://localhost:8080")
	_ = http.ListenAndServe(":8080", proxyHandler)
}

func mustPanic[T any](v T, err error) T {
	if err != nil {
		panic(err)
	}
	return v
}
