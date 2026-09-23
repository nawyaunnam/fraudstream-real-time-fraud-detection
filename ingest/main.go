package main

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/segmentio/kafka-go"
)

type transaction struct {
	TransactionID string  `json:"transaction_id"`
	UserID        string  `json:"user_id"`
	MerchantID    string  `json:"merchant_id"`
	Amount        float64 `json:"amount"`
}

func handler(writer *kafka.Writer) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		defer r.Body.Close()
		var tx transaction
		decoder := json.NewDecoder(http.MaxBytesReader(w, r.Body, 64<<10))
		decoder.DisallowUnknownFields()
		if err := decoder.Decode(&tx); err != nil || tx.TransactionID == "" || tx.UserID == "" || tx.MerchantID == "" || tx.Amount <= 0 {
			http.Error(w, "invalid transaction", http.StatusBadRequest)
			return
		}
		body, _ := json.Marshal(tx)
		ctx, cancel := context.WithTimeout(r.Context(), 3*time.Second)
		defer cancel()
		if err := writer.WriteMessages(ctx, kafka.Message{Key: []byte(tx.UserID), Value: body}); err != nil {
			http.Error(w, "broker unavailable", http.StatusServiceUnavailable)
			return
		}
		w.WriteHeader(http.StatusAccepted)
		_, _ = w.Write([]byte(`{"status":"accepted"}`))
	}
}

func main() {
	brokers := strings.Split(env("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"), ",")
	writer := &kafka.Writer{Addr: kafka.TCP(brokers...), Topic: "transactions", Balancer: &kafka.Hash{}, RequiredAcks: kafka.RequireAll, BatchTimeout: 10 * time.Millisecond}
	defer writer.Close()
	mux := http.NewServeMux()
	mux.HandleFunc("/health", func(w http.ResponseWriter, _ *http.Request) { _, _ = w.Write([]byte(`{"status":"ok"}`)) })
	mux.HandleFunc("/v1/transactions", handler(writer))
	server := &http.Server{Addr: ":8080", Handler: mux, ReadHeaderTimeout: 3 * time.Second, ReadTimeout: 5 * time.Second, WriteTimeout: 5 * time.Second, IdleTimeout: 30 * time.Second}
	log.Fatal(server.ListenAndServe())
}

func env(key, fallback string) string {
	if value := os.Getenv(key); value != "" { return value }
	return fallback
}

