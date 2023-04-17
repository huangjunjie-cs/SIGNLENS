import os

import pandas as pd
import networkx as nx
import numpy as np

from texttable import Texttable
from collections import Counter
import matplotlib.pyplot as plt

from .utils import SignedTriadFeaExtra, SignedBipartiteFeaExtra


class SignLensBase:
    def __init__(self) -> None:
        raise NotImplementedError("Subclasses should implement this")

    def calc_node_num(self) -> int:
        """
        calculate the number of nodes

        Returns
        -------
        int
            the node number
        """
        raise NotImplementedError("Subclasses should implement this")

    def calc_edge_num(self) -> int:
        """
        calculate the number of edges

        Returns
        -------
        int
            the edge number
        """
        raise NotImplementedError("Subclasses should implement this")

    def calc_sign_dist(self) -> tuple:
        """
        calculate sign distribution

        Returns
        -------
        tuple
            (positive edge number, negative edge number, pos_neg_ratio)
        """
        raise NotImplementedError("Subclasses should implement this")

    def report_signed_metrics(self):
        """
        report_signed_metrics print signed social networks analysis metrics


        Returns
        -------
        NoneType
        """
        raise NotImplementedError("Subclasses should implement this")


class SignLens(SignLensBase):
    """
    SignLens is a class for analyzing signed networks.
    """

    def __init__(self, edgelist_fpath, seperator='\t', header=None):
        """
        __init__ sign_lens class for signed graph modeling

        It is used for analyzing signed directed networks

        Parameters
        ----------
        edgelist_fpath : str
            It is the file path for analyzing.
        seperator : str, optional
            The file seperator, by default '\t'
        """
        self.edgelist_fpath = edgelist_fpath
        self.edge_df = pd.read_csv(self.edgelist_fpath,
                                   sep=seperator,
                                   header=header)
        self.edge_df.columns = ['source_node', 'target_node', 'sign']

        node_list = set(self.edge_df.target_node.tolist() +
                        self.edge_df.source_node.tolist())
        self.node_dict = {i: ind for ind, i in enumerate(node_list)}
        self.edge_df['source_node'] = self.edge_df['source_node'].apply(
            lambda x: self.node_dict[x])
        self.edge_df['target_node'] = self.edge_df['target_node'].apply(
            lambda x: self.node_dict[x])

        self.G = nx.DiGraph(self.edge_df[['source_node',
                                          'target_node']].values.tolist())
        pos_edge = self.edge_df[self.edge_df['sign'] > 0]
        self.pos_G = nx.DiGraph(pos_edge[['source_node',
                                          'target_node']].values.tolist())
        neg_edge = self.edge_df[self.edge_df['sign'] < 0]
        self.neg_G = nx.DiGraph(neg_edge[['source_node',
                                          'target_node']].values.tolist())

    def report_signed_metrics(self, output_dir='output') -> str:
        r"""
        Report signed metrics for a signed network.

        The main signed network metrics include *sign distribution*, *balanced triangle distrubition*, *signed in-degree distribution*, *signed out-degree distribution*, *in-degree distribution*, *out-degree distribution*, *hop plot* and *singular value distribution* according to this paper: `"BalanSiNG: Fast and Scalable Generation of Realistic Signed Networks" <https://openproceedings.org/2020/conf/edbt/paper_102.pdf>`_.

        Parameters
        ----------
        output_dir : str, optional
            It will output some figures to the ourput_dir, by default 'output'

        Returns
        -------
        str
            The table for signed metrics.
        """
        args = {}

        pos_num, neg_num, pos_r = self.calc_sign_dist()
        args['The number of nodes'] = self.calc_node_num()
        args['The number of edges (+, -, total)'] = (pos_num, neg_num, pos_num + neg_num)
        args['sign distribution (+)'] = pos_r

        triads_dist, b_ratio, u_ratio = self.calc_signed_triads_dist()
        args['balanced triangle distribution'] = b_ratio
        args['unbalanced triangle distribution'] = u_ratio
        args['signed triangle  (+++, ++-, +--, ---)'] = tuple(
            [round(i, 4) for i in triads_dist])

        # export plot for degree distributions
        G_in_degree, pos_G_in_degree, neg_G_in_degree = self.calc_signed_in_degree(
        )
        G_out_degree, pos_G_out_degree, neg_G_out_degree = self.calc_signed_in_degree(
        )

        fnames = ['In-degree', 'Out-degree']
        datas = [(G_in_degree, pos_G_in_degree, neg_G_in_degree),
                 (G_out_degree, pos_G_out_degree, neg_G_out_degree)]

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        for fname, data in zip(fnames, datas):
            data0, data1, data2 = data

            fig, ax = plt.subplots()
            fpath = os.path.join(output_dir, fname + '.pdf')
            cc = Counter(list(data0.values()))
            ax.scatter(cc.keys(), cc.values(), s=60, alpha=0.9, edgecolors="k")
            ax.set_xscale("log")
            ax.set_yscale("log")
            ax.set_xlabel(fname)
            ax.set_ylabel('Count')
            ax.set_aspect(1. / ax.get_data_ratio())
            ax.figure.savefig(fpath)
            args[f'{fname}output'] = fpath

            fpath = os.path.join(output_dir, fname + '-sign.pdf')
            fig, ax = plt.subplots()
            cc = Counter(list(data1.values()))
            ax.scatter(cc.keys(),
                       cc.values(),
                       s=60,
                       alpha=0.7,
                       color='g',
                       label='Positive')
            cc = Counter(list(data2.values()))
            ax.scatter(cc.keys(),
                       cc.values(),
                       s=60,
                       alpha=0.7,
                       color="r",
                       label='Negative')

            ax.set_xscale("log")
            ax.set_yscale("log")
            ax.set_xlabel(fname)
            ax.set_ylabel('Count')
            ax.legend()
            ax.set_aspect(1. / ax.get_data_ratio())
            ax.figure.savefig(fpath)
            args[f'{fname} sign output'] = fpath

        # plot hopcnt
        fname = 'Hop'
        fpath = os.path.join(output_dir, fname + '.pdf')
        res = self.calc_hop_dist()
        cc = Counter(list(res.values()))
        fig, ax = plt.subplots()
        ax.scatter(cc.keys(), cc.values(), s=60, alpha=0.7, color='b')
        ax.set_yscale("log")
        ax.set_xlabel(fname)
        ax.set_ylabel('Count')
        ax.set_aspect(1. / ax.get_data_ratio())
        ax.figure.savefig(fpath)
        args[f'{fname} sign output'] = fpath

        # plot Sigular Value
        sv = self.calc_singular_value_dist()
        ind = range(1, len(sv) + 1)
        fig, ax = plt.subplots()
        ax.scatter(ind[:100], sv[:100])
        ax.margins(x=0)
        ax.set_ylim([1, 100])
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel('Top-k')
        ax.set_ylabel('Singular Values')
        ax.set_aspect(1. / ax.get_data_ratio())
        fpath = os.path.join(output_dir, 'Top-K.pdf')
        ax.figure.savefig(fpath)
        args['Singular value distribution'] = fpath

        keys = args.keys()
        t = Texttable()
        t.add_rows([["Metrics", "Value"]] +
                   [[k.replace("_", " ").capitalize(), args[k]] for k in keys])
        print(t.draw())

    def calc_node_num(self) -> int:
        r"""
        calculate the number of nodes

        Returns
        -------
        int
            the node number
        """
        node_list = self.edge_df.target_node.tolist(
        ) + self.edge_df.source_node.tolist()
        return len(set(node_list))

    def calc_edge_num(self) -> int:
        r"""
        calculate the number of edges

        Returns
        -------
        int
            the edge number
        """
        return len(self.edge_df)

    def calc_sign_dist(self) -> tuple:
        r"""
        calculate sign distribution

        Returns
        -------
        tuple
            (positive edge number, negative edge number, pos_neg_ratio)
        """
        pos_num = len(self.edge_df[self.edge_df['sign'] > 0])
        neg_num = len(self.edge_df[self.edge_df['sign'] < 0])

        return (pos_num, neg_num, pos_num / (pos_num + neg_num))

    def calc_signed_in_degree(self) -> tuple:
        r"""
        calculate signed in degree

        Returns
        -------
        tuple
            (G_in_degree, pos_G_in_degree, neg_G_in_dergee)
        """
        G_in_degree = {i[0]: i[1] for i in self.G.in_degree()}
        pos_G_in_degree = {i[0]: i[1] for i in self.pos_G.in_degree()}
        neg_G_in_dergee = {i[0]: i[1] for i in self.neg_G.in_degree()}

        return (G_in_degree, pos_G_in_degree, neg_G_in_dergee)

    def calc_signed_out_degree(self) -> tuple:
        r"""
        calculate signed out degree

        Returns
        -------
        tuple
            (G_in_degree, pos_G_in_degree, neg_G_in_dergee)
        """
        G_out_degree = {i[0]: i[1] for i in self.G.out_degree()}
        pos_G_out_degree = {i[0]: i[1] for i in self.pos_G.out_degree()}
        neg_G_out_dergee = {i[0]: i[1] for i in self.neg_G.out_degree()}

        return (G_out_degree, pos_G_out_degree, neg_G_out_dergee)

    def calc_hop_dist(self) -> dict:
        r"""
        calculate the distrubiton of hops

        Returns
        -------
        dict
            the dict of ``{'d': counts }``
        """
        short_dict = {i[0]: i[1] for i in nx.shortest_path_length(self.G)}
        hop_dist = {}
        v_max = 0
        for i, v in short_dict.items():
            for j, k in v.items():
                key = tuple((i, j))
                if not np.isinf(k):
                    hop_dist[key] = k
                    if k > v_max:
                        v_max = k
        return hop_dist

    def calc_singular_value_dist(self) -> np.array:
        r"""
        calculated singular value distribution

        Returns
        -------
            return the svd results of undirected unsigned matrice
        """
        uG = self.G.to_undirected()
        A = nx.to_numpy_matrix(uG)
        u, s, vh = np.linalg.svd(A, full_matrices=True)
        return s

    def calc_balanced_triangle_dist(self) -> tuple:
        r"""
        calculate balanced triangle distributions

        Returns
        -------
        tuple
            (balanced triads, unbalanced triads)
        """
        model = SignedTriadFeaExtra(self.edgelist_fpath, undirected=False)
        s0, s1, s2, s3 = model.calc_balance_and_status_triads_num()
        ratio = (s1 + s2) / s0
        return ratio, 1 - ratio

    def calc_signed_triads_dist(self) -> tuple:
        r"""
        calculate signed triads distributions

        Returns
        -------
        tuple
            ((+++, ++-, +--, ---), balanced triads, unbalanced triads)
        """
        model = SignedTriadFeaExtra(self.edgelist_fpath, undirected=False)
        res = model.calc_balance_triads_dist()
        # +++ ++- +-- ---
        b_triad = res[0] + res[2]
        u_triad = res[1] + res[3]
        return res, b_triad, u_triad


class SignBipartiteLens(SignLensBase):
    def __init__(self, edgelist_fpath, seperator='\t', header=None):
        self.edgelist_fpath = edgelist_fpath
        self.seperator = seperator
        self.edge_df = pd.read_csv(self.edgelist_fpath,
                                   sep=seperator,
                                   header=header)
        self.edge_df.columns = ['node_u', 'node_v', 'sign']

    def calc_signed_bipartite_butterfly_dist(self):
        model = SignedBipartiteFeaExtra(self.edgelist_fpath, seperator=self.seperator, header=None)
        signs, res = model.calc_signed_butterfly_dist()
        return signs, res

    def calc_node_num(self) -> int:
        r"""
        calculate the number of nodes

        Returns
        -------
        int
            the node number
        """
        node_list1 = set(self.edge_df.node_u.tolist())
        node_list2 = set(self.edge_df.node_v.tolist())
        return len(set(node_list1)), len(set(node_list2))

    def calc_edge_num(self) -> int:
        r"""
        calculate the number of edges

        Returns
        -------
        int
            the edge number
        """
        return len(self.edge_df)

    def calc_sign_dist(self) -> tuple:
        r"""
        calculate sign distribution

        Returns
        -------
        tuple
            (positive edge number, negative edge number, pos_neg_ratio)
        """
        pos_num = len(self.edge_df[self.edge_df['sign'] > 0])
        neg_num = len(self.edge_df[self.edge_df['sign'] < 0])

        return (pos_num, neg_num, pos_num / (pos_num + neg_num))

    def report_signed_metrics(self, output_dir='output') -> str:
        args = {}

        args['The number of nodes'] = self.calc_node_num()
        pos_num, neg_num, pos_r = self.calc_sign_dist()
        args['The number of edges (+, -, total)'] = (pos_num, neg_num, pos_num + neg_num)
        args['sign distribution (+)'] = pos_r
        signs, res = self.calc_signed_butterfly_dist()
        args['balanced butterfly distribution'] = sum(res[:-2])
        args['unbalanced butterfly distribution'] = sum(res[-2:])
        sign_str = ",".join(signs)
        args[f'signed butterfly ({sign_str})'] = [round(i, 3) for i in res]

        keys = args.keys()
        t = Texttable()
        t.add_rows([["Metrics", "Value"]] +
                   [[k.replace("_", " ").capitalize(), args[k]] for k in keys])
        print(t.draw())
