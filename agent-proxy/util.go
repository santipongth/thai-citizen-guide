package main

import (
	"bytes"
	"fmt"
	"io"
	"net/http"
	"strings"
)

func GetCurlCommand(req *http.Request) (string, error) {
	var command []string
	command = append(command, fmt.Sprintf("curl -X %s", req.Method))

	// 1. Append Headers
	for name, values := range req.Header {
		for _, value := range values {
			command = append(command, fmt.Sprintf("-H '%s: %s'", name, value))
		}
	}

	// 2. Append Body
	if req.Body != nil {
		bodyBytes, err := io.ReadAll(req.Body)
		if err != nil {
			return "", err
		}
		// Restore the body so it can be read again by the actual HTTP client
		req.Body = io.NopCloser(bytes.NewBuffer(bodyBytes))

		if len(bodyBytes) > 0 {
			command = append(command, fmt.Sprintf("-d '%s'", string(bodyBytes)))
		}
	}

	// 3. Append URL
	command = append(command, fmt.Sprintf("'%s'", req.URL.String()))

	return strings.Join(command, " "), nil
}
