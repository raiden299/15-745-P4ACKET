package main

import (
	"context"
	"fmt"
	"log"
	"time"

	p4 "github.com/p4lang/p4runtime/go/p4/v1"
	"google.golang.org/grpc"
)

type P4RuntimeClient struct {
	client               p4.P4RuntimeClient
	deviceID             uint64
	stream               p4.P4Runtime_StreamChannelClient
	arbitration_complete chan bool
}

func NewP4RuntimeClient(address string, deviceID uint64) (*P4RuntimeClient, error) {
	fmt.Printf("Connecting to P4Runtime server at %s...\n", address)
	conn, err := grpc.Dial(address, grpc.WithInsecure())
	if err != nil {
		return nil, fmt.Errorf("failed to connect to P4Runtime server: %v", err)
	}

	client := p4.NewP4RuntimeClient(conn)
	stream, err := client.StreamChannel(context.Background())
	if err != nil {
		return nil, fmt.Errorf("failed to create stream channel: %v", err)
	}

	return &P4RuntimeClient{
		client:               client,
		deviceID:             deviceID,
		stream:               stream,
		arbitration_complete: make(chan bool),
	}, nil
}

func (c *P4RuntimeClient) SetupCloneSession(sessionID uint32, egressPort uint32) error {
	cloneSessionEntry := &p4.CloneSessionEntry{
		SessionId:         sessionID,
		ClassOfService:    1,
		PacketLengthBytes: 0,
		Replicas: []*p4.Replica{
			{
				PortKind: &p4.Replica_EgressPort{EgressPort: egressPort},
				Instance: 0,
			},
		},
	}

	_, err := c.client.Write(context.Background(), &p4.WriteRequest{
		DeviceId: c.deviceID,
		Updates: []*p4.Update{
			{
				Type: p4.Update_INSERT,
				Entity: &p4.Entity{
					Entity: &p4.Entity_PacketReplicationEngineEntry{
						PacketReplicationEngineEntry: &p4.PacketReplicationEngineEntry{
							Type: &p4.PacketReplicationEngineEntry_CloneSessionEntry{
								CloneSessionEntry: cloneSessionEntry,
							},
						},
					},
				},
			},
		},
	})
	return err
}

func (c *P4RuntimeClient) StreamMessages() {
	go func() {
		for {
			select {
			case <-c.arbitration_complete:
				fmt.Println("Arbitration complete")
				return
			default:
				fmt.Println("Sending arbitration message...")
				arbitration := &p4.StreamMessageRequest{
					Update: &p4.StreamMessageRequest_Arbitration{
						Arbitration: &p4.MasterArbitrationUpdate{
							DeviceId: c.deviceID,
							ElectionId: &p4.Uint128{
								High: 0,
								Low:  1,
							},
						},
					},
				}
				if err := c.stream.Send(arbitration); err != nil {
					log.Fatalf("Failed to send arbitration message: %v", err)
				}
				time.Sleep(2 * time.Second)
			}
		}
	}()
}

func (c *P4RuntimeClient) ReceivePackets() {
	for {
		response, err := c.stream.Recv()
		if err != nil {
			log.Fatalf("Failed to receive response: %v", err)
		}
		fmt.Printf("Received response: %v\n", response)
		if arbitration := response.GetArbitration(); arbitration != nil {
			c.arbitration_complete <- true
		} else if packet := response.GetPacket(); packet != nil {
			c.HandlePacketIn(packet)
		}
	}
}

func (c *P4RuntimeClient) HandlePacketIn(packet *p4.PacketIn) {
	fmt.Printf("Received packet: %v\n", packet)
}

func main() {
	address := "0.0.0.0:50051"
	deviceID := uint64(0)
	client, err := NewP4RuntimeClient(address, deviceID)
	if err != nil {
		log.Fatalf("Failed to create P4Runtime client: %v", err)
	}

	fmt.Println("Listening for packets...")
	client.SetupCloneSession(100, 16)
	client.StreamMessages()
	client.ReceivePackets()
}
