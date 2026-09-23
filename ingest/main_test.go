package main

import "testing"

func TestEnvFallback(t *testing.T) {
	t.Setenv("FRAUDSTREAM_TEST_VALUE", "")
	if value := env("FRAUDSTREAM_TEST_VALUE", "fallback"); value != "fallback" {
		t.Fatalf("expected fallback, got %s", value)
	}
}

