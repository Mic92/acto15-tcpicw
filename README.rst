===========================================
 Impact of TCP's Initial Congestion Window
===========================================

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
