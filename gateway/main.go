// gateway/main.go
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"time"
)

type HealthResponse struct {
	Service   string            `json:"service"`
	Status    string            `json:"status"`
	Timestamp string            `json:"timestamp"`
	Services  map[string]string `json:"services"`
}

type ProxyConfig struct {
	UserService         string
	OrderService        string
	NotificationService string
}

func getEnv(key, fallback string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return fallback
}

var config ProxyConfig

func main() {
	config = ProxyConfig{
		UserService:         getEnv("USER_SERVICE_URL",         "http://user-service:5000"),
		OrderService:        getEnv("ORDER_SERVICE_URL",        "http://order-service:8080"),
		NotificationService: getEnv("NOTIFICATION_SERVICE_URL", "http://notification-service:3000"),
	}

	mux := http.NewServeMux()

	// Health check
	mux.HandleFunc("/health", healthHandler)

	// Proxy routes to each service
	mux.HandleFunc("/api/users",         proxyHandler(config.UserService))
	mux.HandleFunc("/api/users/",        proxyHandler(config.UserService))
	mux.HandleFunc("/api/orders",        proxyHandler(config.OrderService))
	mux.HandleFunc("/api/orders/",       proxyHandler(config.OrderService))
	mux.HandleFunc("/api/notifications", proxyHandler(config.NotificationService))
	mux.HandleFunc("/api/notifications/",proxyHandler(config.NotificationService))

	port := getEnv("PORT", "8081")
	log.Printf("Gateway running on port %s", port)
	log.Fatal(http.ListenAndServe(":"+port, mux))
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	services := map[string]string{
		"user-service":         checkService(config.UserService + "/health"),
		"order-service":        checkService(config.OrderService + "/actuator/health"),
		"notification-service": checkService(config.NotificationService + "/health"),
	}

	status := "healthy"
	for _, s := range services {
		if s != "up" {
			status = "degraded"
		}
	}

	resp := HealthResponse{
		Service:   "api-gateway",
		Status:    status,
		Timestamp: time.Now().Format(time.RFC3339),
		Services:  services,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func checkService(url string) string {
	client := &http.Client{Timeout: 2 * time.Second}
	resp, err := client.Get(url)
	if err != nil || resp.StatusCode != 200 {
		return "down"
	}
	return "up"
}

func proxyHandler(target string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		url := target + r.URL.Path
		if r.URL.RawQuery != "" {
			url += "?" + r.URL.RawQuery
		}

		req, err := http.NewRequest(r.Method, url, r.Body)
		if err != nil {
			http.Error(w, "Bad request", http.StatusBadRequest)
			return
		}

		// Forward headers
		for key, vals := range r.Header {
			for _, val := range vals {
				req.Header.Add(key, val)
			}
		}

		client := &http.Client{Timeout: 10 * time.Second}
		resp, err := client.Do(req)
		if err != nil {
			http.Error(w, fmt.Sprintf("Service unavailable: %v", err), http.StatusServiceUnavailable)
			return
		}
		defer resp.Body.Close()

		// Forward response headers and status
		for key, vals := range resp.Header {
			for _, val := range vals {
				w.Header().Add(key, val)
			}
		}
		w.WriteHeader(resp.StatusCode)
		io.Copy(w, resp.Body)
	}
}