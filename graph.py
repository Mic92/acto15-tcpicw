import seaborn as sns
import pandas as pd

sns.set(style="whitegrid", font_scale=1.7)

RELATIV_FIELDS = ["time_total"]


def relative_to_initcwnd3(df):
    relative_to = None
    for cwnd in df['initcwnd'].unique():
        by_cwnd = df[df.initcwnd == cwnd]
        by_cwnd3 = df[df.initcwnd == 3]
        on = ["delay", "bandwidth", "max_queue_size", "request_size"]
        merged = by_cwnd.merge(by_cwnd3, on=on)
        data = {}
        for field in RELATIV_FIELDS:
            data["relative_" + field] = merged[field + "_x"] / merged[field + "_y"]

        for field in merged.columns.values:
            if field.endswith("_x"):
                data[field[:-2]] = merged[field]
        for field in on:
            data[field] = merged[field]
        data['initcwnd'] = cwnd

        if relative_to is None:
            relative_to = pd.DataFrame(data)
        else:
            relative_to = relative_to.append(pd.DataFrame(data))
    return relative_to

# Load the example Titanic dataset
df = pd.read_csv('data.csv', sep='\t')
df['transmission_time'] = df['last_packet'] - df['first_packet']
# reasonable = df[df.transmission_time > 0]
# reasonable.drop('transmission_time', 1)
# reasonable.to_csv("data.csv", sep='\t', index=False)

df = relative_to_initcwnd3(df)

#    for cwnd in [3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 18, 24, 32, 40]:
#        for delay in [1, 5, 10, 50, 100]:
#            for bw in [1, 2, 5, 10, 100]:
#                for max_queue_size in [1000]:  # reasonable values?
#                    for request_size in range(15):
#
#df = df[(df.bandwidth == 100) & (df.request_size == 256) & (df.delay == 10)]
#df = df[(df.request_size == 256) & (df.delay == 10)]
#df = df[(df.request_size == 256) & (df.bandwidth == 100)]

df = df[(df.request_size.isin([16, 128, 1024])) &
        (df.delay.isin([5, 50, 300]))]

#for request_size in df.request_size.unique():
#    # Draw a nested barplot to show survival for class and sex
#    g = sns.factorplot(x="initcwnd",
#                       y="relative_time_total",
#                       col="bandwidth",
#                       row="delay",
#                       data=df[(df.request_size == request_size)],
#                       kind="bar",
#                       palette="muted")
#    g.set(xlim=(.5, None))
#    g.despine(left=True)
#    print("request_size-%dkb.pdf" % request_size)
#    g.savefig("request_size-%dkb.pdf" % request_size, dpi=300)
#

RELATIV = "Time relative to initcwnd=3"
SIZE = "Request size"
df.rename(columns={'relative_time_total': RELATIV, "request_size": SIZE},
          inplace=True)

for bandwidth in df.bandwidth.unique():
    # Draw a nested barplot to show survival for class and sex
    g = sns.factorplot(x="initcwnd",
                       y=RELATIV,
                       col="delay",
                       row=SIZE,
                       data=df[(df.bandwidth == bandwidth)],
                       kind="bar",
                       palette="muted",
                       aspect=1.2)
    g.set(ylim=(.5, None))
    g.despine(left=True)
    print("bandwidth-%dmb.pdf" % bandwidth)
    g.savefig("bandwidth-%dmb.pdf" % bandwidth, dpi=300)

# initcwnd
# delay
# bandwidth
# max_queue_size
# request_size

