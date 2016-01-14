# Impact of TCP's Initial Congestion Window

TCP flows start with an initial congestion window of at most three segments or
about 4KB of data. Because most Web transactions are short-lived, the initial
congestion window is a critical TCP parameter in determining how quickly flows
can finish. To optimize the user experience for Web transactions it has been
suggested to increase the initial congestion window.

The task is to investigate the impact of the congestion window size on the
throughput of short lived transactions. Mininet should be used for the
experimental setup. The performance for different initial congestion window
sizes and transaction times should be measured with iperf. The results should
then be presented with a graph.


## Test setup

- Client <- 1Gbit/s -> Router <- Uplink -> Server
- Client: curl, HTTP-Header von Chrome
- Server: Nginx 1.8.0

The following test parameter were used:

- initial window size (on both links): 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 18, 24, 32, 40
- uplink delay in ms: 1, 5, 10, 50, 100, 300
- uplink bandwith in mbit/s: 1, 2, 5, 10, 100
- requests size in kb (only payload, not http): 1, 2, 4, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096,
  8192, 16384
