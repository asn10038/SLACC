from __future__ import print_function, division
import sys
import os
sys.path.append(os.path.abspath("."))
sys.dont_write_bytecode = True

__author__ = "bigfatnoob"

from utils import cache
from utils.lib import O
from sklearn.cluster import dbscan
import numpy as np
import scipy as sp
from scipy import stats
from collections import defaultdict
from utils.uf import UnionFind

FUNCTION_FILE = "data/cfiles_dump/fuzzed/uniform.pkl"


class Point(O):
  def __init__(self):
    O.__init__(self)
    self.outputs = []
    self.errors = []
    self.function_body = None
    self.return_type = None
    self.cluster_id = None

  @staticmethod
  def from_function(function):
    if function['results'] is None: return None
    point = Point()
    for result in function['results']:
      if result[1] is not None:
        point.outputs.append(result[1])
      else:
        point.errors.append(result[2])
    point.function_body = function['function'].body
    point.return_type = function['function'].ret.type
    return point


class Clusterer(O):
  def __init__(self, functions):
    O.__init__(self)
    self.points = pre_process(functions)
    self.X = np.arange(len(self.points)).reshape(-1, 1)

  def distance(self, x, y):
    point_a = self.points[int(x)]
    point_b = self.points[int(y)]
    if point_a.return_type != point_b.return_type:
      return 1
    return 1

  def cosine_distance(self, x, y):
    point_a = self.points[int(x)]
    point_b = self.points[int(y)]
    a_outputs = set(point_a.outputs)
    b_outputs = set(point_b.outputs)
    all_words = set().union(a_outputs).union(b_outputs)
    a_vector, b_vector = [], []
    for word in all_words:
      a_vector.append(1 if word in a_outputs else 0)
      b_vector.append(1 if word in b_outputs else 0)
    return np.dot(a_vector, b_vector) / (np.linalg.norm(a_vector) * np.linalg.norm(b_vector))

  def ks_distance(self, x, y):
    point_a = self.points[int(x)]
    point_b = self.points[int(y)]
    a_outputs = point_a.outputs
    b_outputs = point_b.outputs
    if len(a_outputs) == 0 or len(b_outputs) == 0:
      return 1.0
    similarity, significance = stats.ks_2samp(a_outputs, b_outputs)
    if significance > 0.1:
      return 1.0 - similarity
    return 1.0

  def cluster(self):
    ret_groups = defaultdict(list)
    rets = set()
    arguments = {
        "float": (self.ks_distance, 0.25, 2),
        "int": (self.ks_distance, 0.025, 5),
        "char": (self.ks_distance, 0.5, 2)
    }
    ret_points = defaultdict(list)
    for point, x in zip(self.points, self.X):
      rets.add(point.return_type)
      ret_groups[point.return_type].append(x)
      ret_points[point.return_type].append(point)
    for ret_type, group in ret_groups.items():
      argument = arguments[ret_type]
      _, cluster_labels = dbscan(group, metric=argument[0], eps=argument[1], min_samples=argument[2])
      noise = sum([1 if label == -1 else 0 for label in cluster_labels])
      for point, cluster_label in zip(ret_points[ret_type], cluster_labels):
        if cluster_label == -1:
          point.cluster_id = "OUTLIER"
        else:
          point.cluster_id = "%s-%d" % (ret_type, cluster_label)
      print(ret_type, len(group), noise, set(cluster_labels))
    point_clusters = []
    for points in ret_points.items():
      point_clusters.append(points)
    cache.save("data/cfiles_dump/clusters/dbscan.pkl", point_clusters)

  def clones(self):
    ret_groups = defaultdict(list)
    ret_points = defaultdict(list)
    rets = set()
    for point, x in zip(self.points, self.X):
      rets.add(point.return_type)
      ret_groups[point.return_type].append(x)
      ret_points[point.return_type].append(point)
    for ret_type, points in ret_points.items():
      uf = UnionFind(points)
      for p in points:
        if len(p.outputs) == 0: continue
        for q in points:
          if uf.find(p, q) or len(q.outputs) == 0: continue
          # if set(p.outputs) == set(q.outputs):
          if sorted(p.outputs) == sorted(q.outputs):
            uf.union(p, q)
      # Bookmarks for stats
      direct_clones = []
      grouped = 0
      outputs_in_clusters = defaultdict(int)
      methods_in_clusters = defaultdict(int)
      for cluster in uf.get_clusters():
        if len(cluster) > 1:
          ## Test
          # for i in range(min(3, len(cluster))):
          #   print(cluster[i].function_body)
          #   print(cluster[i].outputs)
          # exit()
          output_size = len(set(cluster[0].outputs))
          if output_size >= 7:
            output_size = "7+"
          outputs_in_clusters[output_size] += 1
          methods_in_clusters[output_size] += len(cluster)
          grouped += len(cluster)
          direct_clones.append(cluster)
      result = O(
          ret_type=ret_type,
          n_methods=len(points),
          n_direct_clones_cluster=len(direct_clones),
          n_no_clones=len(points) - grouped,
          num_clusters_wrt_size=outputs_in_clusters,
          num_methods_in_clusters_wrt_size=methods_in_clusters
      )
      print(result)
      # clones = []
      # n_pts = len(points)
      # for i in range(n_pts):
      #   if len(points[i].outputs) == 0: continue
      #   f_clones = []
      #   for j in range(i, n_pts):
      #     if i == j or len(points[j].outputs) == 0: continue
      #     if set(points[i].outputs) == set(points[j].outputs):
      #       f_clones.append(points[j])
      #   if len(f_clones) > 0:
      #     clones.append({
      #         "function": points[i],
      #         "clones": f_clones
      #     })
      # print(len(clones))
    # TODO: Implement set union



def pre_process(functions):
  points = []
  for function in functions.values():
    point = Point.from_function(function)
    if point is not None:
      points.append(point)
  return points


def _main():
  functions = cache.load(FUNCTION_FILE)
  clusterer = Clusterer(functions)
  # dbscan(np.arange(len(points)).reshape(-1, 1), metric=clusterer.distance, eps=5, min_samples=2)
  clusterer.clones()
  # TODO: Create a class for dbscan and use that to cluser with a custom metric



if __name__ == "__main__":
  _main()