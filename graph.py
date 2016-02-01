import seaborn as sns
import pandas as pd

sns.set(style="whitegrid", font_scale=1.7)

RELATIV_FIELDS = ["time_total", "duplicate_acks_b2a"]


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

df = pd.read_csv('data.csv', sep='\t')
df['transmission_time'] = df['last_packet'] - df['first_packet']

df = relative_to_initcwnd3(df)

RELATIV = "Time relative to initcwnd=3"
SIZE = "Request size"
df.rename(columns={'relative_time_total': RELATIV, "request_size": SIZE},
          inplace=True)


def draw_graphs(df, y, file_prefix, format="png"):
    for request_size in df[SIZE].unique():
        # Draw a nested barplot to show survival for class and sex
        g = sns.factorplot(x="initcwnd",
                           y=y,
                           col="bandwidth",
                           row="delay",
                           data=df[(df[SIZE] == request_size)],
                           kind="bar",
                           palette="muted")
        g.set(xlim=(.5, None))
        g.despine(left=True)
        name = "%s-request_size-%dkb.%s" % (file_prefix, request_size, format)
        print(name)
        g.savefig(name, dpi=300)

    for bandwidth in df.bandwidth.unique():
        # Draw a nested barplot to show survival for class and sex
        g = sns.factorplot(x="initcwnd",
                           y=y,
                           col="delay",
                           row=SIZE,
                           data=df[(df.bandwidth == bandwidth)],
                           kind="bar",
                           palette="muted",
                           aspect=1.2)
        g.set(ylim=(.5, None))
        g.despine(left=True)
        name = "%s-bandwidth-%dmb.%s" % (file_prefix, bandwidth, format)
        print(name)
        g.savefig(name, dpi=100)

draw_graphs(df, RELATIV, "time", ".png")
#draw_graphs(df, "relative_duplicate_acks_b2a", "dupacks", "png")


# initcwnd
# delay
# bandwidth
# max_queue_size
# request_size

#df = df[(df.request_size.isin([16, 128, 1024])) &
#        (df.delay.isin([5, 50, 300]))]
#RELATIV = "Time relative to initcwnd=3"
#SIZE = "Request size"
#df.rename(columns={'relative_time_total': RELATIV, "request_size": SIZE},
#          inplace=True)
#
#for bandwidth in df.bandwidth.unique():
#    # Draw a nested barplot to show survival for class and sex
#    g = sns.factorplot(x="initcwnd",
#                       y=RELATIV,
#                       col="delay",
#                       row=SIZE,
#                       data=df[(df.bandwidth == bandwidth)],
#                       kind="bar",
#                       palette="muted",
#                       aspect=1.2)
#    g.set(ylim=(.5, None))
#    g.despine(left=True)
#    print("bandwidth-%dmb.pdf" % bandwidth)
#    g.savefig("bandwidth-%dmb.pdf" % bandwidth, dpi=300)
