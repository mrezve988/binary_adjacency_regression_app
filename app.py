
import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import tempfile
from pyvis.network import Network
import streamlit.components.v1 as components

st.set_page_config(page_title="Room Plan Optimizer (Merged)", layout="wide")
st.title("🏗️ Room Plan Optimizer with Bubble Graphs + Adjacency + Circulation")

ROOMS = ["Living", "Dining", "Kitchen", "Store", "Toilet1", "Bedroom1", "Bath1", "Bedroom2", "Bedroom3"]

IDEAL_EDGES = [
    ("Living", "Dining"), ("Dining", "Toilet1"), ("Dining", "Kitchen"), ("Kitchen", "Store"),
    ("Living", "Bedroom1"), ("Bedroom1", "Bath1"), ("Living", "Bedroom2"), ("Bedroom2", "Toilet1"),
    ("Living", "Bedroom3"), ("Bedroom3", "Toilet1")
]

IDEAL_SIZES = {
    "Living": 22, "Dining": 12, "Kitchen": 10, "Store": 2.5, "Toilet1": 2.5,
    "Bedroom1": 13, "Bath1": 4, "Bedroom2": 10, "Bedroom3": 10
}

# Build graph from edge list
def build_graph(edges):
    G = nx.Graph()
    for room in ROOMS:
        G.add_node(room)
    for u, v in edges:
        if u in ROOMS and v in ROOMS:
            G.add_edge(u, v)
    return G

# Bubble graph visualization
def display_graph_pyvis(G, sizes_dict):
    net = Network(height="500px", width="100%", bgcolor="#ffffff", font_color="black")
    for node in G.nodes:
        size = sizes_dict.get(node, 10)
        net.add_node(node, label=node, value=size)
    for u, v in G.edges:
        net.add_edge(u, v)
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
    net.save_graph(tmp_file.name)
    return tmp_file.name

# Circulation simulation (linear regression-like logic)
def simulate_center_distance(u, v):
    base = 3 if "Toilet" in u or "Toilet" in v else 5
    extra = 0.5 if "Living" in [u, v] else 0
    return base + extra + np.random.normal(0, 0.2)

def total_circulation_distance(G):
    return round(sum(simulate_center_distance(u, v) for u, v in G.edges), 2)

# Suggest improvements
def suggest_improvements(ideal_graph, user_graph, ideal_sizes, user_sizes):
    suggestions = []
    for u, v in ideal_graph.edges:
        if not user_graph.has_edge(u, v):
            suggestions.append(f"Missing connection: {u} ↔ {v}")
    for room in ideal_sizes:
        if abs(ideal_sizes[room] - user_sizes.get(room, 0)) / ideal_sizes[room] > 0.2:
            suggestions.append(f"Check size of {room}: ideal is {ideal_sizes[room]} m²")
    return suggestions

# UI: Room Sizes
st.subheader("🔹 Step 1: Enter Room Sizes")
user_sizes = {}
for room, default in IDEAL_SIZES.items():
    user_sizes[room] = st.number_input(f"{room} size (m²)", min_value=1.0, value=float(default), key=room)

# UI: User Adjacency Input
st.subheader("🔹 Step 2: Enter Your Room Adjacencies")
user_input = st.text_area("Input format: one connection per line, e.g. 'Living, Dining'", 
                          value="Living, Dining\nDining, Kitchen\nKitchen, Store\nLiving, Bedroom1\nBedroom1, Bath1\nLiving, Bedroom2\nBedroom2, Toilet1\nLiving, Bedroom3\nBedroom3, Toilet1")

def parse_user_edges(text):
    edges = []
    for line in text.strip().split("\n"):
        try:
            u, v = map(str.strip, line.split(","))
            edges.append((u, v))
        except:
            continue
    return edges

if st.button("Evaluate Plan"):
    user_edges = parse_user_edges(user_input)
    ideal_graph = build_graph(IDEAL_EDGES)
    user_graph = build_graph(user_edges)

    score_adjacency = sum(1 for u, v in IDEAL_EDGES if user_graph.has_edge(u, v)) / len(IDEAL_EDGES)
    circ_ideal = total_circulation_distance(ideal_graph)
    circ_user = total_circulation_distance(user_graph)

    st.markdown("### 📊 Results")
    st.markdown(f"✅ **Adjacency Match Score**: `{score_adjacency:.2f}`")
    st.markdown(f"📏 **Ideal Circulation**: `{circ_ideal} units`")
    st.markdown(f"📏 **Your Plan Circulation**: `{circ_user} units`")

    if circ_user > circ_ideal:
        st.warning("⚠️ Your plan has higher estimated circulation than the ideal.")
    else:
        st.success("🎯 Your plan is more efficient or equally optimized.")

    suggestions = suggest_improvements(ideal_graph, user_graph, IDEAL_SIZES, user_sizes)
    if suggestions:
        st.markdown("### 🛠 Suggestions to Improve Your Plan")
        for s in suggestions:
            st.markdown(f"- {s}")
    else:
        st.success("👍 No major suggestions. Great job!")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🧭 Ideal Plan")
        html_ideal = display_graph_pyvis(ideal_graph, IDEAL_SIZES)
        with open(html_ideal, "r", encoding="utf-8") as f:
            components.html(f.read(), height=500, scrolling=True)
    with col2:
        st.markdown("### ✏️ Your Plan")
        html_user = display_graph_pyvis(user_graph, user_sizes)
        with open(html_user, "r", encoding="utf-8") as f:
            components.html(f.read(), height=500, scrolling=True)
