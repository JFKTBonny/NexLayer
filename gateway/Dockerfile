# gateway/Dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod .
COPY main.go .
RUN go mod download && go build -o gateway .

FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/gateway .
EXPOSE 8081
CMD ["./gateway"]