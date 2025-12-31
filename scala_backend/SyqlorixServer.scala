//> using lib "org.apache.thrift:libthrift:0.19.0"
//> using lib "org.slf4j:slf4j-simple:2.0.9"
//> using source "gen-java"

import org.apache.thrift.server.TServer
import org.apache.thrift.server.TThreadPoolServer
import org.apache.thrift.transport.TServerSocket
import org.apache.thrift.transport.TServerTransport
import syqlorix.thrift.*
import java.util.HashMap

class SyqlorixHandler extends SyqlorixService.Iface {
  override def render(request: ThriftRequest): ThriftResponse = {
    println(f"Received request for path: ${request.getPath}")
    
    val response = new ThriftResponse()
    response.setHtml("<h1>Rendered by Scala Backend!</h1><p>Path: " + request.getPath + "</p>")
    response.setStatusCode(200)
    val headers = new HashMap[String, String]()
    headers.put("Content-Type", "text/html")
    response.setHeaders(headers)
    response
  }
}

object SyqlorixServer {
  def main(args: Array[String]): Unit = {
    try {
      val handler = new SyqlorixHandler()
      val processor = new SyqlorixService.Processor(handler)
      val serverTransport = new TServerSocket(9090)
      val server = new TThreadPoolServer(new TThreadPoolServer.Args(serverTransport).processor(processor))

      println("Starting the Scala Syqlorix server...")
      server.serve()
    } catch {
      case e: Exception => e.printStackTrace()
    }
  }
}
