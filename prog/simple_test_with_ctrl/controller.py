import grpc
from p4.v1 import p4runtime_pb2
from p4.v1 import p4runtime_pb2_grpc

class P4RuntimeClient:
    def __init__(self, address, device_id):
        self.channel = grpc.insecure_channel(address)
        self.stub = p4runtime_pb2_grpc.P4RuntimeStub(self.channel)
        self.device_id = device_id
        self.stream = self.stub.StreamChannel(self.stream_messages())

    def stream_messages(self):
        while True:
            yield p4runtime_pb2.StreamMessageRequest(
                arbitration=p4runtime_pb2.MasterArbitrationUpdate(
                    device_id=self.device_id,
                    election_id=p4runtime_pb2.Uint128(high=0, low=1)
                )
            )

    def receive_packets(self):
        for response in self.stream:
            if response.HasField("packet"):
                self.handle_packet_in(response.packet)

    def handle_packet_in(self, packet_in):
        print(f"Received packet: {packet_in}")

if __name__ == "__main__":
    address = "0.0.0.0:50051"
    device_id = 0
    client = P4RuntimeClient(address, device_id)
    print("Listening for packets...")
    client.receive_packets()