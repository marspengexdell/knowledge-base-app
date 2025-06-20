
import grpc
from concurrent import futures
from app.protos import inference_pb2_grpc, inference_pb2
from app.services.model_service import generate_response

class InferenceServicer(inference_pb2_grpc.InferenceServiceServicer):
    def Generate(self, request, context):
        result = generate_response(request.prompt)
        return inference_pb2.InferenceReply(response=result)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    inference_pb2_grpc.add_InferenceServiceServicer_to_server(InferenceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("gRPC server started on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
