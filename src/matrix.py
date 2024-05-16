import os
import pandas as pd
from sklearn.cluster import KMeans
import warnings
import plotly.express as px
import pdb


warnings.filterwarnings("ignore")

folder_path = "/Users/tanujnamdeo/Desktop/AAC/annotation/src/data/trimmed_csv"


# Load the data from a CSV file
def load_csv(file_path):
    data = pd.read_csv(file_path)
    return data


# Normalize the result
def normalize(result):
    for i in range(len(result)):
        total = sum(result[i])
        if total == 0:
            continue
        for j in range(len(result[i])):
            result[i][j] = round(result[i][j] / total, 2)
    return result


# Calculate the similarity between two clusters
def norm_sim(cluster1, cluster2):
    return longest_common_subsequence(cluster1, cluster2) / max(
        len(cluster1), len(cluster2)
    )


# Apply the KMeans algorithm
def apply_kmeans(dataframe, columns, n_clusters=20):
    kmeans_columns = dataframe[columns].copy()
    kmeans_columns.dropna(inplace=True)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    kmeans.fit(kmeans_columns)
    cluster_ids = kmeans.labels_
    centroids = kmeans.cluster_centers_
    dataframe["cluster_id"] = cluster_ids
    return dataframe, cluster_ids, centroids


# Longest common subsequence
def longest_common_subsequence(cluster1, cluster2):
    m = len(cluster1)
    n = len(cluster2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if cluster1[i - 1] == cluster2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    return dp[m][n]


# Combine the files from the two samples
def combine_file(csv_files):
    combined_data = pd.DataFrame()
    for file in csv_files:
        file_path = os.path.join(folder_path, file)
        data = load_csv(file_path)
        data["gesture_id"] = file.split(".")[0]
        combined_data = combined_data.append(data)

    return combined_data


# Process the data
def process_data(prefix, weights, combined_data, files1, files2):
    result_tot = [[0] * (len(files1)) for _ in range(len(files1))]
    combined_data_orig = combined_data.copy()
    for k in range(len(prefix)):
        columns = []

        for p in prefix[k]:
            columns += [p + "_x", p + "_y", p + "_z"]

        combined_data = combined_data_orig.copy()

        combined_data = combined_data[columns + ["gesture_id"]].copy()
        combined_data.dropna(inplace=True)

        # Apply kmeans on the combined data
        combined_data, _, _ = apply_kmeans(combined_data, columns, n_clusters=20)

        result = [[0] * (len(files1)) for _ in range(len(files1))]

        for i in range(len(files1)):
            for j in range(len(files2)):
                cluster1 = combined_data[
                    combined_data["gesture_id"] == files1[i].split(".")[0]
                ]
                cluster2 = combined_data[
                    combined_data["gesture_id"] == files2[j].split(".")[0]
                ]
                result[i][j] = norm_sim(
                    cluster1["cluster_id"].tolist(), cluster2["cluster_id"].tolist()
                )

        for i in range(len(result)):
            for j in range(len(result[i])):
                result_tot[i][j] += result[i][j] * weights[k][0]

    for i in range(len(result_tot)):
        for j in range(len(result_tot[i])):
            result_tot[i][j] = round(result_tot[i][j], 2)

    return result_tot


# Generate the heatmap data
def heatmap_data(prefix, weights):
    csv_files = [file for file in os.listdir(folder_path) if file.endswith(".csv")]
    csv_files.sort()
    combined_data = combine_file(csv_files)
    result = process_data(
        prefix,
        weights,
        combined_data,
        csv_files,
        csv_files,
    )
    return result, csv_files


# Return the similarity between two gestures
def similartiy_gesture(prefix, weights, gesture_1, gesture_2):
    csv_files = [file for file in os.listdir(folder_path) if file.endswith(".csv")]
    csv_files.sort()
    combined_data = combine_file(csv_files)
    result = process_data(
        prefix,
        weights,
        combined_data,
        csv_files,
        csv_files,
    )

    for i in range(len(csv_files)):
        if csv_files[i].split(".")[0] == gesture_1:
            index1 = i
        if csv_files[i].split(".")[0] == gesture_2:
            index2 = i

    return result[index1][index2]
