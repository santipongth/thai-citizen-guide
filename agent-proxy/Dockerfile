from golang:1.26-alpine as development
workdir /app
run go install github.com/air-verse/air@v1.65.1
copy . .
cmd ["air", "-c", ".air.toml"]

from golang:1.26-alpine as builder
workdir /app
copy go.mod go.sum ./
run go mod download
copy . .
run CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /app/agent-proxy .

from alpine as production
run apk --no-cache add ca-certificates
workdir /app
copy --from=builder /app/agent-proxy .
expose 8080
cmd ["/app/agent-proxy"]