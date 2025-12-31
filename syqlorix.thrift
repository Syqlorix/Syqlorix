namespace py syqlorix.thrift
namespace scala syqlorix.thrift

struct ThriftRequest {
  1: string method,
  2: string path,
  3: map<string, string> headers,
  4: map<string, string> query_params,
  5: map<string, string> form_data,
  6: binary body
}

struct ThriftResponse {
  1: string html,
  2: i32 status_code,
  3: map<string, string> headers
}

service SyqlorixService {
  ThriftResponse render(1: ThriftRequest request)
}
