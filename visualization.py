import json

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

out = []

with open("out/results_2023-06-20.json", "r") as f:
    out_dict = json.load(f)
    results = out_dict["results"]
    for task_id, metrics in results.items():
        task_name = task_id.split("_")[0]
        num_fewshots = int(task_id.split("_")[-3])
        stratified = task_id.split("_")[-1] == "stratified"
        for metric_name, metric_val in metrics.items():
            out.append(
                {
                    "task": task_name,
                    "num_fewshots": num_fewshots,
                    "stratified": stratified,
                    "metric": metric_name,
                    "val": metric_val,
                }
            )

df = pd.DataFrame(out)

# Get unique tasks and metrics
tasks = df["task"].unique()

# Streamlit app
st.title("Metric Values for Different Stratified Values")

# Sidebar selection
selected_task = st.sidebar.selectbox("Select a task", tasks)
filtered_df = df[df["task"] == selected_task]

metrics = filtered_df["metric"].unique()
selected_metric = st.sidebar.selectbox("Select a metric", metrics)
filtered_df = filtered_df[filtered_df["metric"] == selected_metric]

print(filtered_df)

# Filter the DataFrame based on selected task and metric

# Line plots
chart = (
    alt.Chart(filtered_df)
    .mark_line()
    .encode(x="num_fewshots:O", y="val:Q", color="stratified:N")
)

st.altair_chart(chart, use_container_width=True)
