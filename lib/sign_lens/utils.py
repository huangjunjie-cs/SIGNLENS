
import os
import numpy as np
import scipy.sparse as sp
from collections import defaultdict
from tqdm import tqdm


class SignedTriadFeaExtra:

    def __init__(self, edgelist_fpath, undirected=False, seperator='\t'):
        self.undirected = undirected
        self.seperator = seperator

        res = self.init_edgelists(edgelist_fpath)
        self.pos_in_edgelists, self.pos_out_edgelists, self.neg_in_edgelists, self.neg_out_edgelists = res

    def init_edgelists(self, edgelist_fpath):
        pos_out_edgelists = defaultdict(list)
        neg_out_edgelists = defaultdict(list)
        pos_in_edgelists = defaultdict(list)
        neg_in_edgelists = defaultdict(list)
        with open(edgelist_fpath) as f:
            for line in f.readlines():
                x, y, z = line.split(self.seperator)
                x = int(x)
                y = int(y)
                z = int(z)
                if z == 1:
                    pos_out_edgelists[x].append(y)
                    pos_in_edgelists[y].append(x)
                else:
                    neg_out_edgelists[x].append(y)
                    neg_in_edgelists[y].append(x)

                if self.undirected:
                    # if undireced, repeat it
                    x, y = y, x
                    if z == 1:
                        pos_out_edgelists[x].append(y)
                        pos_in_edgelists[y].append(x)
                    else:
                        neg_out_edgelists[x].append(y)
                        neg_in_edgelists[y].append(x)

        return pos_in_edgelists, pos_out_edgelists, neg_in_edgelists, neg_out_edgelists

    def get_pos_indegree(self, v):
        return len(self.pos_in_edgelists[v])

    def get_pos_outdegree(self, v):
        return len(self.pos_out_edgelists[v])

    def get_neg_indegree(self, v):
        return len(self.neg_in_edgelists[v])

    def get_neg_outdegree(self, v):
        return len(self.neg_out_edgelists[v])

    def common_neighbors(self, u, v):
        u_neighbors = self.pos_in_edgelists[u] + self.neg_in_edgelists[u] + \
            self.pos_out_edgelists[u] + self.neg_out_edgelists[u]
        v_neighbors = self.pos_in_edgelists[v] + self.neg_in_edgelists[v] + \
            self.pos_out_edgelists[v] + self.neg_out_edgelists[v]
        return len(set(u_neighbors).intersection(set(v_neighbors)))

    def extract_triad_counts(self, u, v) -> tuple:
        r"""

        .. math::

            A \times B \alpha


        """
        d1_1 = len(set(self.pos_out_edgelists[u]).intersection(set(self.pos_in_edgelists[v])))
        d1_2 = len(set(self.pos_out_edgelists[u]).intersection(set(self.neg_in_edgelists[v])))
        d1_3 = len(set(self.neg_out_edgelists[u]).intersection(set(self.pos_in_edgelists[v])))
        d1_4 = len(set(self.neg_out_edgelists[u]).intersection(set(self.neg_in_edgelists[v])))

        d2_1 = len(set(self.pos_out_edgelists[u]).intersection(set(self.pos_out_edgelists[v])))
        d2_2 = len(set(self.pos_out_edgelists[u]).intersection(set(self.neg_out_edgelists[v])))
        d2_3 = len(set(self.neg_out_edgelists[u]).intersection(set(self.pos_out_edgelists[v])))
        d2_4 = len(set(self.neg_out_edgelists[u]).intersection(set(self.neg_out_edgelists[v])))

        d3_1 = len(set(self.pos_in_edgelists[u]).intersection(set(self.pos_out_edgelists[v])))
        d3_2 = len(set(self.pos_in_edgelists[u]).intersection(set(self.neg_out_edgelists[v])))
        d3_3 = len(set(self.neg_in_edgelists[u]).intersection(set(self.pos_out_edgelists[v])))
        d3_4 = len(set(self.neg_in_edgelists[u]).intersection(set(self.neg_out_edgelists[v])))

        d4_1 = len(set(self.pos_in_edgelists[u]).intersection(set(self.pos_in_edgelists[v])))
        d4_2 = len(set(self.pos_in_edgelists[u]).intersection(set(self.neg_in_edgelists[v])))
        d4_3 = len(set(self.neg_in_edgelists[u]).intersection(set(self.pos_in_edgelists[v])))
        d4_4 = len(set(self.neg_in_edgelists[u]).intersection(set(self.neg_in_edgelists[v])))

        return d1_1, d1_2, d1_3, d1_4, d2_1, d2_2, d2_3, d2_4, d3_1, d3_2, d3_3, d3_4, d4_1, d4_2, d4_3, d4_4

    def calc_balance_triads_num(self):
        s0, s1, s2, s3 = self.calc_balance_and_status_triads_num()
        return s1 + s2, s0

    def calc_balance_triads_dist(self):
        t1 = []  # +++
        t2 = []  # ++-
        t3 = []  # +--
        t4 = []  # ---
        for x in list(self.pos_out_edgelists):
            for y in self.pos_out_edgelists[x]:
                mask1 = [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]  # +++
                mask2 = [0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0]  # ++-
                mask3 = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]  # +--
                mask4 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # ---
                rs = self.extract_triad_counts(x, y)
                t1.append(np.dot(mask1, rs))
                t2.append(np.dot(mask2, rs))
                t3.append(np.dot(mask3, rs))
                t4.append(np.dot(mask4, rs))

        for x in list(self.neg_out_edgelists):
            for y in self.neg_out_edgelists[x]:
                mask1 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # +++
                mask2 = [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]  # ++-
                mask3 = [0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0]  # +--
                mask4 = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]  # ---
                rs = self.extract_triad_counts(x, y)
                t1.append(np.dot(mask1, rs))
                t2.append(np.dot(mask2, rs))
                t3.append(np.dot(mask3, rs))
                t4.append(np.dot(mask4, rs))

        s1 = np.sum(t1)
        s2 = np.sum(t2)
        s3 = np.sum(t3)
        s4 = np.sum(t4)
        res = np.array([s1, s2, s3, s4])

        return res / res.sum()

    def calc_balance_and_status_triads_num(self):
        rs0 = []
        rs1 = []
        rs2 = []
        rs3 = []
        for x in list(self.pos_out_edgelists):
            for y in self.pos_out_edgelists[x]:
                mask1 = [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1]  # both satify
                mask2 = [0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]  # only balance
                mask3 = [0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0]  # only status
                rs = self.extract_triad_counts(x, y)
                rs0.append(rs)
                rs1.append(np.dot(mask1, rs))
                rs2.append(np.dot(mask2, rs))
                rs3.append(np.dot(mask3, rs))

        for x in list(self.neg_out_edgelists):
            for y in self.neg_out_edgelists[x]:
                mask1 = [0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0]
                mask2 = [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0]
                mask3 = [0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1]
                rs = self.extract_triad_counts(x, y)
                rs0.append(rs)
                rs1.append(np.dot(mask1, rs))
                rs2.append(np.dot(mask2, rs))
                rs3.append(np.dot(mask3, rs))

        s0 = np.sum(rs0)
        s1 = np.sum(rs1)
        s2 = np.sum(rs2)
        s3 = np.sum(rs3)
        print('all triangle', s0)
        print('both', s1, s1 / s0)
        print('balance', s2, s2 / s0)
        print('status', s3, s3 / s0)
        return s0, s1, s2, s3


class SignedTriadFeaExtraByMatrace:

    def __init__(self, edgelist_fpath, undirected=False, seperator='\t'):
        self.undirected = undirected
        self.seperator = seperator
        self.init_matrice(edgelist_fpath)

    def init_matrice(self, edgelist_fpath):
        pos_edgelist = []
        neg_edgelist = []
        node_set = {}
        with open(edgelist_fpath) as f:
            for line in f:
                x, y, z = line.strip().split(self.seperator)
                if x not in node_set:
                    node_set[x] = len(node_set)
                if y not in node_set:
                    node_set[y] = len(node_set)

                x = int(x)
                y = int(y)
                z = int(z)
                if z == 1:
                    pos_edgelist.append((x, y))
                else:
                    neg_edgelist.append((x, y))

        node_num = len(node_set)

        pos_edge_array = np.array(pos_edgelist)
        neg_edge_array = np.array(neg_edgelist)

        row = pos_edge_array[:, 0]
        col = pos_edge_array[:, 1]
        data = np.ones_like(pos_edge_array[:, 0])
        self.pos_mat = sp.coo_matrix((data, (row, col)), shape=(node_num, node_num))

        row = neg_edge_array[:, 0]
        col = neg_edge_array[:, 1]
        data = np.ones_like(neg_edge_array[:, 0])
        self.neg_mat = sp.coo_matrix((data, (row, col)), shape=(node_num, node_num))

    def calc_balance_and_status_triads_num(self):
        r"""
        calc_balance_and_status_triads_num 
        .. math::

            {A_1^+} \cdot {A_1^+} \odot (1 - I)\odot {A_1^+} 


        """
        A_plus = self.pos_mat
        A_minus = self.neg_mat
        ts = [
            [(A_plus, A_plus), (A_plus, A_minus), (A_minus, A_plus), (A_minus, A_minus)],
            [(A_plus, A_plus.T), (A_plus, A_minus.T), (A_minus, A_plus.T), (A_minus, A_minus.T)],
            [(A_plus.T, A_plus.T), (A_plus.T, A_minus.T), (A_minus.T, A_plus.T), (A_minus.T, A_minus.T)],
            [(A_plus.T, A_plus), (A_plus.T, A_minus), (A_minus.T, A_plus), (A_minus.T, A_minus)],
        ]

        rs0 = []
        rs1 = []
        rs2 = []
        rs3 = []
        # pos
        rs = []
        for t in ts:
            for a, b in t:
                res = np.dot(a, b)
                res.setdiag(0)
                res = res.multiply(A_plus)
                rs.append(res.sum())
        mask1 = [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1]  # both satify
        mask2 = [0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]  # only balance
        mask3 = [0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0]  # only status
        rs = np.array(rs)
        rs0.append(rs)
        rs1.append(np.dot(mask1, rs))
        rs2.append(np.dot(mask2, rs))
        rs3.append(np.dot(mask3, rs))

        rs = []
        for t in ts:
            for a, b in t:
                res = np.dot(a, b)
                res.setdiag(0)
                res = res.multiply(A_minus)
                rs.append(res.sum())
        mask1 = [0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0]
        mask2 = [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0]
        mask3 = [0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1]

        rs = np.array(rs)
        rs0.append(rs)
        rs1.append(np.dot(mask1, rs))
        rs2.append(np.dot(mask2, rs))
        rs3.append(np.dot(mask3, rs))

        s0 = np.sum(rs0)
        s1 = np.sum(rs1)
        s2 = np.sum(rs2)
        s3 = np.sum(rs3)

        print('all triangle', s0)
        print('both', s1, s1 / s0)
        print('balance', s2, s2 / s0)
        print('status', s3, s3 / s0)
        return s0, s1, s2, s3


class SignedBipartiteFeaExtra:

    def __init__(self, edgelist_fpath, seperator='\t', header=None) -> None:
        self.edgelist_fpath = edgelist_fpath
        self.seperator = seperator
        self.init_edgelists()

    def init_edgelists(self):
        self.pos_a_b = defaultdict(set)
        self.pos_b_a = defaultdict(set)
        self.neg_a_b = defaultdict(set)
        self.neg_b_a = defaultdict(set)

        edges = []
        with open(self.edgelist_fpath) as f:
            for line in f:
                a, b, s = map(int, line.strip().split(self.seperator))
                edges.append((a, b, s))
                if s > 0:
                    self.pos_a_b[a].add(b)
                    self.pos_b_a[b].add(a)
                else:
                    self.neg_a_b[a].add(b)
                    self.neg_b_a[a].add(a)
        self.edges = np.array(edges)

    def count_values(self, a_b_1, a_b_2, a_b_3, a_b_4, a1, a2):
        b1 = a_b_1[a1]
        b2 = a_b_2[a1]
        b3 = a_b_3[a2]
        b4 = a_b_4[a2]
        aa = b1.intersection(b3)
        bb = b2.intersection(b4)
        cnt1 = len(aa)
        cnt2 = len(bb)
        return cnt1 * cnt2 - len(aa.intersection(bb))

    def calc_signed_bipartite_butterfly_dist(self):

        a_set = set([i[0] for i in self.edges])
        mapper = {'++++': 0, '----': 0, '++--': 0, '+-+-': 0, '+--+': 0, '+---': 0, '+++-': 0}

        for a1 in tqdm(a_set):
            for a2 in a_set:
                if a1 == a2:
                    continue
                mapper['++++'] += self.count_values(self.pos_a_b, self.pos_a_b, self.pos_a_b, self.pos_a_b, a1, a2)
                mapper['++--'] += self.count_values(self.pos_a_b, self.pos_a_b, self.neg_a_b, self.neg_a_b, a1, a2)
                mapper['+++-'] += self.count_values(self.pos_a_b, self.pos_a_b, self.pos_a_b, self.neg_a_b, a1, a2)
                mapper['+---'] += self.count_values(self.pos_a_b, self.neg_a_b, self.neg_a_b, self.neg_a_b, a1, a2)
                mapper['+-+-'] += self.count_values(self.pos_a_b, self.neg_a_b, self.pos_a_b, self.neg_a_b, a1, a2)
                mapper['+--+'] += self.count_values(self.pos_a_b, self.neg_a_b, self.neg_a_b, self.pos_a_b, a1, a2)
                mapper['----'] += self.count_values(self.neg_a_b, self.neg_a_b, self.neg_a_b, self.neg_a_b, a1, a2)

        sum_s = sum(mapper.values())
        res_sign = [
            '++++',
            '+--+',
            '++--',
            '+-+-',
            '----',
            '+++-',
            '+---'
        ]
        return res_sign, [mapper[i]/sum_s for i in res_sign]


class SignedBipartiteFeaExtraByMatrace:

    def __init__(self, edgelist_fpath, seperator='\t', header=None) -> None:
        self.edgelist_fpath = edgelist_fpath
        self.seperator = seperator
        self.init_matrice(edgelist_fpath)

    def init_matrice(self, edgelist_fpath):
        pos_edgelist = []
        neg_edgelist = []
        node_set1 = {}
        node_set2 = {}
        with open(edgelist_fpath) as f:
            for line in f.readlines():
                x, y, z = line.strip().split(self.seperator)
                if x not in node_set1:
                    node_set1[x] = len(node_set1)
                if y not in node_set2:
                    node_set2[y] = len(node_set2)

                x = int(x)
                y = int(y)
                z = int(z)
                if z == 1:
                    pos_edgelist.append((x, y))
                else:
                    neg_edgelist.append((x, y))

        node_num1 = len(node_set1)
        node_num2 = len(node_set2)

        pos_edge_array = np.array(pos_edgelist)
        neg_edge_array = np.array(neg_edgelist)

        row = pos_edge_array[:, 0]
        col = pos_edge_array[:, 1]
        data = np.ones_like(pos_edge_array[:, 0])
        self.pos_mat = sp.coo_matrix((data, (row, col)), shape=(node_num1, node_num2))

        row = neg_edge_array[:, 0]
        col = neg_edge_array[:, 1]
        data = np.ones_like(neg_edge_array[:, 0])
        self.neg_mat = sp.coo_matrix((data, (row, col)), shape=(node_num1, node_num2))

    def calc_signed_bipartite_butterfly_dist(self):

        mapper = {'++++': 0, '----': 0, '++--': 0, '+-+-': 0, '+--+': 0, '+---': 0, '+++-': 0}
        mapper_operataions = [
            [self.pos_mat, self.pos_mat.T, self.pos_mat, self.pos_mat.T],
            [self.neg_mat, self.neg_mat.T, self.neg_mat, self.neg_mat.T],
            [self.pos_mat, self.pos_mat.T, self.neg_mat, self.neg_mat.T],
            [self.pos_mat, self.neg_mat.T, self.pos_mat, self.neg_mat.T],
            [self.pos_mat, self.neg_mat.T, self.neg_mat, self.pos_mat.T],
            [self.pos_mat, self.neg_mat.T, self.neg_mat, self.neg_mat.T],
            [self.pos_mat, self.pos_mat.T, self.pos_mat, self.neg_mat.T],
        ]
        for map, operation in zip(mapper.keys(), mapper_operataions):
            a, b, c, d = operation
            res = a.dot(b)
            res.setdiag(0)
            res = res.dot(c)
            res = res.dot(d)
            v = res.diagonal().sum()
            mapper[map] = v

        sum_s = sum(mapper.values())
        res_sign = [
            '++++',
            '+--+',
            '++--',
            '+-+-',
            '----',
            '+++-',
            '+---'
        ]
        return res_sign, [mapper[i]/sum_s for i in res_sign]


class SignedPathFeaExtraByMatrace:
     
    def __init__(self, edgelist_fpath, nodefea_fpath, seperator='\t', header=None) -> None:
        self.edgelist_fpath = edgelist_fpath
        self.nodefea_fpath  = nodefea_fpath
        self.seperator = seperator
        self.init_matrice(edgelist_fpath)


    def init_matrice(self, edgelist_fpath):
        pos_edgelist = []
        neg_edgelist = []
        node_set1 = {}
        node_set2 = {}


    def compute_path(self):
        pass



if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    test_fpath = os.path.abspath(os.path.join(BASE_DIR, '..', 'tests', 'test_datas', 'simple_case.edgelist'))
    model = SignedTriadFeaExtra(edgelist_fpath=test_fpath)
    model.calc_balance_and_status_triads_num()
