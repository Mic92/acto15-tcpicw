import seaborn as sns
import pandas as pd

sns.set(style="whitegrid")

RELATIV_FIELDS = ["time_total"]


def relative_to_initcwnd3(df):
    relative_to = None
    for cwnd in df['initcwnd'].unique():
        by_cwnd = df[df.initcwnd == cwnd]
        by_cwnd3 = df[df.initcwnd == 3]
        on = ["delay", "bandwith", "max_queue_size", "request_size"]
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
#df = df[(df.bandwith == 100) & (df.request_size == 256) & (df.delay == 10)]
#df = df[(df.request_size == 256) & (df.delay == 10)]
#df = df[(df.request_size == 256) & (df.bandwith == 100)]

for request_size in df.request_size.unique():
    # Draw a nested barplot to show survival for class and sex
    g = sns.factorplot(x="initcwnd",
                       y="relative_time_total",
                       col="bandwith",
                       row="delay",
                       data=df[(df.request_size == request_size)],
                       kind="bar",
                       palette="muted")
    g.despine(left=True)
    print("request_size-%dkb.png" % request_size)
    g.savefig("request_size-%dkb.png" % request_size, dpi=300)

for bandwith in df.bandwith.unique():
    # Draw a nested barplot to show survival for class and sex
    g = sns.factorplot(x="initcwnd",
                       y="relative_time_total",
                       col="request_size",
                       row="delay",
                       data=df[(df.bandwith == bandwith)],
                       kind="bar",
                       palette="muted")
    g.despine(left=True)
    print("bandwith-%dmb.png" % bandwith)
    g.savefig("bandwith-%dmb.png" % bandwith, dpi=300)

# initcwnd
# delay
# bandwith
# max_queue_size
# request_size

#g.set_ylabels("survival probability")
