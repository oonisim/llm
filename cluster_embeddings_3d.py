"""
Cluster embedding vectors and visualize in 3D space.

This script demonstrates:
1. Generating or loading embedding vectors
2. Reducing dimensionality to 3D using UMAP, PCA, or t-SNE
3. Clustering using KMeans or DBSCAN
4. Interactive 3D visualization with plotly
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import umap
import plotly.graph_objects as go
import plotly.express as px
from typing import Tuple, Optional, List


def generate_sample_embeddings(n_samples: int = 500, n_dimensions: int = 768) -> np.ndarray:
    """
    Generate sample embedding vectors for demonstration.

    Args:
        n_samples: Number of embedding vectors to generate
        n_dimensions: Dimensionality of embeddings (e.g., 768 for BERT, 1536 for OpenAI)

    Returns:
        Array of shape (n_samples, n_dimensions)
    """
    # Create 3 clusters in high-dimensional space
    cluster1 = np.random.randn(n_samples // 3, n_dimensions) + np.array([2.0] * n_dimensions)
    cluster2 = np.random.randn(n_samples // 3, n_dimensions) + np.array([-2.0] * n_dimensions)
    cluster3 = np.random.randn(n_samples // 3, n_dimensions)

    embeddings = np.vstack([cluster1, cluster2, cluster3])
    np.random.shuffle(embeddings)

    return embeddings


def reduce_dimensions(
    embeddings: np.ndarray,
    method: str = 'umap',
    n_components: int = 3,
    random_state: int = 42,
    **kwargs
) -> np.ndarray:
    """
    Reduce embedding dimensions to 3D for visualization.

    Args:
        embeddings: High-dimensional embeddings
        method: 'umap', 'pca', or 'tsne'
        n_components: Number of dimensions (typically 3 for 3D viz)
        random_state: Random seed
        **kwargs: Additional arguments for the dimensionality reduction algorithm
            UMAP: n_neighbors (default=15), min_dist (default=0.1), metric (default='cosine')
            t-SNE: perplexity (default=30)

    Returns:
        Reduced embeddings of shape (n_samples, n_components)
    """
    if method.lower() == 'umap':
        n_neighbors = kwargs.get('n_neighbors', 15)
        min_dist = kwargs.get('min_dist', 0.1)
        metric = kwargs.get('metric', 'cosine')
        reducer = umap.UMAP(
            n_components=n_components,
            n_neighbors=n_neighbors,
            min_dist=min_dist,
            metric=metric,
            random_state=random_state
        )
        print(f"Using UMAP for dimensionality reduction to {n_components}D")
        print(f"  n_neighbors={n_neighbors}, min_dist={min_dist}, metric={metric}")
    elif method.lower() == 'pca':
        reducer = PCA(n_components=n_components, random_state=random_state)
        print(f"Using PCA for dimensionality reduction to {n_components}D")
    elif method.lower() == 'tsne':
        perplexity = kwargs.get('perplexity', 30)
        reducer = TSNE(n_components=n_components, random_state=random_state, perplexity=perplexity)
        print(f"Using t-SNE for dimensionality reduction to {n_components}D (perplexity={perplexity})")
    else:
        raise ValueError(f"Unknown method: {method}. Use 'umap', 'pca', or 'tsne'")

    reduced = reducer.fit_transform(embeddings)

    if method.lower() == 'pca':
        explained_variance = reducer.explained_variance_ratio_
        print(f"Explained variance ratio: {explained_variance}")
        print(f"Total variance explained: {explained_variance.sum():.2%}")

    return reduced


def cluster_embeddings(
    embeddings: np.ndarray,
    method: str = 'kmeans',
    n_clusters: int = 3,
    **kwargs
) -> np.ndarray:
    """
    Cluster embeddings using specified algorithm.

    Args:
        embeddings: Embedding vectors
        method: 'kmeans' or 'dbscan'
        n_clusters: Number of clusters (for KMeans)
        **kwargs: Additional arguments for clustering algorithm

    Returns:
        Cluster labels for each embedding
    """
    if method.lower() == 'kmeans':
        clusterer = KMeans(n_clusters=n_clusters, random_state=42, **kwargs)
        print(f"Clustering with KMeans (n_clusters={n_clusters})")
    elif method.lower() == 'dbscan':
        eps = kwargs.get('eps', 0.5)
        min_samples = kwargs.get('min_samples', 5)
        clusterer = DBSCAN(eps=eps, min_samples=min_samples)
        print(f"Clustering with DBSCAN (eps={eps}, min_samples={min_samples})")
    else:
        raise ValueError(f"Unknown method: {method}. Use 'kmeans' or 'dbscan'")

    labels = clusterer.fit_predict(embeddings)

    n_clusters_found = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = list(labels).count(-1)
    print(f"Found {n_clusters_found} clusters")
    if n_noise > 0:
        print(f"Noise points: {n_noise}")

    return labels


def visualize_3d_matplotlib(
    embeddings_3d: np.ndarray,
    labels: np.ndarray,
    title: str = "3D Embedding Clusters"
) -> None:
    """
    Visualize 3D embeddings using matplotlib.

    Args:
        embeddings_3d: 3D embeddings
        labels: Cluster labels
        title: Plot title
    """
    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection='3d')

    unique_labels = np.unique(labels)
    colors = plt.cm.tab10(np.linspace(0, 1, len(unique_labels)))

    for label, color in zip(unique_labels, colors):
        mask = labels == label
        label_name = f'Cluster {label}' if label != -1 else 'Noise'
        ax.scatter(
            embeddings_3d[mask, 0],
            embeddings_3d[mask, 1],
            embeddings_3d[mask, 2],
            c=[color],
            label=label_name,
            s=50,
            alpha=0.6
        )

    ax.set_xlabel('Component 1')
    ax.set_ylabel('Component 2')
    ax.set_zlabel('Component 3')
    ax.set_title(title)
    ax.legend()

    plt.tight_layout()
    plt.show()


def visualize_3d_plotly(
    embeddings_3d: np.ndarray,
    labels: np.ndarray,
    text_labels: Optional[List[str]] = None,
    title: str = "3D Embedding Clusters (Interactive)"
) -> go.Figure:
    """
    Create interactive 3D visualization using plotly.

    Args:
        embeddings_3d: 3D embeddings
        labels: Cluster labels
        text_labels: Optional text labels for each point (e.g., document titles)
        title: Plot title

    Returns:
        Plotly figure object
    """
    if text_labels is None:
        text_labels = [f"Point {i}" for i in range(len(embeddings_3d))]

    # Create DataFrame-like structure for plotly
    data = {
        'x': embeddings_3d[:, 0],
        'y': embeddings_3d[:, 1],
        'z': embeddings_3d[:, 2],
        'cluster': labels.astype(str),
        'text': text_labels
    }

    fig = px.scatter_3d(
        data,
        x='x',
        y='y',
        z='z',
        color='cluster',
        hover_data=['text'],
        title=title,
        labels={'x': 'Component 1', 'y': 'Component 2', 'z': 'Component 3'},
        color_discrete_sequence=px.colors.qualitative.Set1
    )

    fig.update_traces(marker=dict(size=5, opacity=0.7))
    fig.update_layout(
        scene=dict(
            xaxis_title='Component 1',
            yaxis_title='Component 2',
            zaxis_title='Component 3'
        ),
        height=800
    )

    return fig


def main():
    """Main execution flow."""
    print("=" * 60)
    print("Embedding Clustering and 3D Visualization")
    print("=" * 60)

    # Step 1: Generate or load embeddings
    print("\n1. Generating sample embeddings...")
    embeddings = generate_sample_embeddings(n_samples=500, n_dimensions=768)
    print(f"Generated embeddings shape: {embeddings.shape}")

    # Step 2: Reduce to 3D using UMAP
    print("\n2. Reducing dimensions to 3D...")
    embeddings_3d_umap = reduce_dimensions(
        embeddings,
        method='umap',
        n_components=3,
        n_neighbors=15,
        min_dist=0.1,
        metric='cosine'
    )

    # Optional: Compare with other methods
    # embeddings_3d_pca = reduce_dimensions(embeddings, method='pca', n_components=3)
    # embeddings_3d_tsne = reduce_dimensions(embeddings, method='tsne', n_components=3, perplexity=30)

    # Step 3: Cluster the embeddings
    print("\n3. Clustering embeddings...")
    labels_kmeans = cluster_embeddings(embeddings_3d_umap, method='kmeans', n_clusters=3)

    # Optional: Try DBSCAN
    # labels_dbscan = cluster_embeddings(embeddings_3d_umap, method='dbscan', eps=1.0, min_samples=10)

    # Step 4: Visualize
    print("\n4. Creating visualizations...")

    # Matplotlib visualization
    print("Creating matplotlib 3D plot...")
    visualize_3d_matplotlib(embeddings_3d_umap, labels_kmeans, title="3D Embedding Clusters (UMAP + KMeans)")

    # Plotly interactive visualization
    print("Creating interactive plotly visualization...")
    fig = visualize_3d_plotly(
        embeddings_3d_umap,
        labels_kmeans,
        title="3D Embedding Clusters - Interactive (UMAP + KMeans)"
    )
    fig.show()

    print("\n" + "=" * 60)
    print("Visualization complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()