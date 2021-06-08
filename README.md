[pypi-image]: https://badge.fury.io/py/torch-geometric.svg
# SIGNLENS

SIGNLENS is a tool that helps to analyze polarized social relationships based on signed graph modeling.

## System Design

![SIGNLENS](./imgs/framework.png?raw=true "The illustration of the proposed SIGNLENS.")


### Individual Analysis

For individual analysis, we usually focus on some specific nodes. 


### Group Analysis
For group analysis, we analyze it with time.


## Data Collection

We give two examples from real-world applications to demonstrate how our system works. 

Here is the [cleaned data link](./datas/readme.md).

### The China Biographical Database (CBDB)

The data is collected from [CBDB](https://projects.iq.harvard.edu/cbdb).

Run the spider by:
```
python get_cbdb_data.py
```

###  United States Congress Vote (USCV) 

The data is collected from [GovTrack.us](https://www.govtrack.us/)

Run the spider by:
```
python get_govtrack_data.py
```

## Data Analysis

After downloading the data, you can get some basic data analysis results by running jupyter notebooks.

### CBDB
For CBDB dataset, you can follow [this jupyter notebook](./ipynbs/cbdb_analysis.ipynb)

![cbdb_sign](./imgs/cbdb_sign.png?raw=true "CBDB")

### USCV
For USCV dataset, you can follow [this jupyter notebook](./ipynbs/uscv_analysis.ipynb)

![house_sign](./imgs/house_sign.png?raw=true "House")


![senate_sign](./imgs/senate_sign.png?raw=true "Senate")

## Developments
This system is a web based system.
This [readme](./development.md) will help you to run it.


Some codes will be updated after the busy weeks. Sorry for the delay! 


## Cite

Please cite [our paper](https://ojs.aaai.org/index.php/ICWSM/article/view/18136)  if you use these codes and datasets in your own work:

```
@inproceedings{huang2021signlens,
  title={SIGNLENS: A Tool for Analyzing People's Polarization Social Relationship Based on Signed Graph Modeling},
  author={Huang, Junjie and Shen, Huawei and Cheng, Xueqi},
  booktitle={Proceedings of the International AAAI Conference on Web and Social Media},
  volume={15},
  pages={1091--1093},
  year={2021}
}
```

Feel free to [email us](mailto:huangjunjie17s@ict.ac.cn) if you wish to improve this project

