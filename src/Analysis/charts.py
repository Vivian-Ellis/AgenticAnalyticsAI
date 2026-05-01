import matplotlib.pyplot as plt
import seaborn as sns

def plot_time_series(df, x, y, title):
    plt.figure(figsize=(12,6))
    plt.plot(df[x], df[y])
    plt.title(title)
    plt.xlabel(x)
    plt.ylabel(y)
    path=f'../chart_files/{title}.png'
    plt.savefig(path)
    plt.close()
    return path

def plot_bar(df, x, y, title):
    plt.figure(figsize=(14,8))
    sns.set_style("whitegrid")
    sns.barplot(
        data=df,
        x=x,
        y=y,
        color="#EAADD4"
    ).set(title=title)

    plt.xticks(rotation=45)

    sns.despine()
    # plt.grid(False)

    path = f'../chart_files/{title}.png'

    plt.savefig(path, bbox_inches='tight', dpi=300)
    plt.close()
    return path
