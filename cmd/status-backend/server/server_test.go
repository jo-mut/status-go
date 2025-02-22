package server

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"testing"
	"time"

	"github.com/stretchr/testify/require"

	"github.com/gorilla/websocket"

	"github.com/status-im/status-go/protocol/common"
	"github.com/status-im/status-go/signal"
)

func setupServer(t *testing.T) (*Server, string) {
	srv := NewServer()
	srv.Setup()
	err := srv.Listen("localhost:0")
	require.NoError(t, err)

	addr := srv.Address()

	// Check URL
	serverURLString := fmt.Sprintf("http://%s", addr)
	serverURL, err := url.Parse(serverURLString)
	require.NoError(t, err)
	require.NotNil(t, serverURL)
	require.NotZero(t, serverURL.Port())

	return srv, addr
}

func shutdownServer(srv *Server) {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	srv.Stop(ctx)
}

func TestSignals(t *testing.T) {
	srv, serverURLString := setupServer(t)
	go srv.Serve()
	defer shutdownServer(srv)

	signalsURL := fmt.Sprintf("ws://%s/signals", serverURLString)
	connection, _, err := websocket.DefaultDialer.Dial(signalsURL, nil)
	require.NoError(t, err)
	require.NotNil(t, connection)
	defer func() {
		err := connection.Close()
		require.NoError(t, err)
	}()

	sentEvent := signal.MessageDeliveredSignal{
		ChatID:    randomAlphabeticalString(t, 10),
		MessageID: randomAlphabeticalString(t, 10),
	}

	signal.SendMessageDelivered(sentEvent.ChatID, sentEvent.MessageID)

	messageType, data, err := connection.ReadMessage()
	require.NoError(t, err)
	require.Equal(t, websocket.TextMessage, messageType)

	receivedSignal := signal.Envelope{}
	err = json.Unmarshal(data, &receivedSignal)
	require.NoError(t, err)
	require.Equal(t, signal.EventMesssageDelivered, receivedSignal.Type)
	require.NotNil(t, receivedSignal.Event)

	// Convert `interface{}` to json and then back to the original struct
	tempJson, err := json.Marshal(receivedSignal.Event)
	require.NoError(t, err)

	receivedEvent := signal.MessageDeliveredSignal{}
	err = json.Unmarshal(tempJson, &receivedEvent)
	require.NoError(t, err)
	require.Equal(t, sentEvent, receivedEvent)
}

func TestMobileAPI(t *testing.T) {
	// Setup fake endpoints
	endpointsWithResponse := EndpointsWithRequest
	endpointsNoRequest := EndpointsWithoutRequest
	endpointsUnsupported := EndpointsUnsupported
	t.Cleanup(func() {
		EndpointsWithRequest = endpointsWithResponse
		EndpointsWithoutRequest = endpointsNoRequest
		EndpointsUnsupported = endpointsUnsupported
	})

	endpointWithResponse := "/" + randomAlphabeticalString(t, 5)
	endpointNoRequest := "/" + randomAlphabeticalString(t, 5)
	endpointUnsupported := "/" + randomAlphabeticalString(t, 5)

	request1 := randomAlphabeticalString(t, 5)
	response1 := randomAlphabeticalString(t, 5)
	response2 := randomAlphabeticalString(t, 5)

	EndpointsWithRequest = map[string]func(string) string{
		endpointWithResponse: func(request string) string {
			require.Equal(t, request1, request)
			return response1
		},
	}
	EndpointsWithoutRequest = map[string]func() string{
		endpointNoRequest: func() string {
			return response2
		},
	}
	EndpointsUnsupported = []string{endpointUnsupported}

	// Setup server
	srv, _ := setupServer(t)
	defer shutdownServer(srv)
	go srv.Serve()
	srv.RegisterMobileAPI()

	requestBody := []byte(request1)
	bodyReader := bytes.NewReader(requestBody)

	port, err := srv.Port()
	require.NoError(t, err)

	serverURL := fmt.Sprintf("http://127.0.0.1:%d", port)

	// Test endpoints with response
	resp, err := http.Post(serverURL+endpointWithResponse, "application/text", bodyReader)
	require.NoError(t, err)
	require.NotNil(t, resp)
	require.Equal(t, http.StatusOK, resp.StatusCode)

	responseBody, err := io.ReadAll(resp.Body)
	require.NoError(t, err)
	require.Equal(t, response1, string(responseBody))

	// Test endpoints with no request
	resp, err = http.Get(serverURL + endpointNoRequest)
	require.NoError(t, err)
	require.NotNil(t, resp)
	require.Equal(t, http.StatusOK, resp.StatusCode)

	responseBody, err = io.ReadAll(resp.Body)
	require.NoError(t, err)
	require.Equal(t, response2, string(responseBody))

	// Test unsupported endpoint
	resp, err = http.Get(serverURL + endpointUnsupported)
	require.NoError(t, err)
	require.NotNil(t, resp)
	require.Equal(t, http.StatusNotImplemented, resp.StatusCode)

}

func randomAlphabeticalString(t *testing.T, n int) string {
	s, err := common.RandomAlphabeticalString(n)
	require.NoError(t, err)
	return s
}
