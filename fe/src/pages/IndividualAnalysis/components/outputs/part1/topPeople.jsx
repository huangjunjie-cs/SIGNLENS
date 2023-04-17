import React from 'react';
import { Divider, Table, Descriptions } from 'antd';

const columns = [
  {
    title: 'EngName',
    dataIndex: 'EngName',
    width: 100,
    fixed: 'left',
    align: 'center'
  },
  {
    title: 'ChName',
    dataIndex: 'ChName',
    width: 100,
    fixed: 'left',
    align: 'center'
  },
  {
    title: 'PersonID',
    dataIndex: 'PersonID',
    render: (value, row, index) => (
      <a href={`https://cbdb.fas.harvard.edu/cbdbapi/person.php?id=${value}`}>
        {value}
      </a>
    ),
    width: 100,
    align: 'center'
  },
  {
    dataIndex: 'c1',
    title: <div><span>Degree</span><br /><span>Centrality</span></div>,
    sorter: (a, b) => a.c1 - b.c1,
    width: 200,
    align: 'center'
  },
  {
    dataIndex: 'c2',
    title: <div><span>Betweeness</span><br /><span>Centrality</span></div>,
    sorter: (a, b) => a.c2 - b.c2,
    width: 200,
    align: 'center'
  },
  {
    dataIndex: 'c3',
    title: <div><span>Closeness</span><br /><span>Centrality</span></div>,
    sorter: (a, b) => a.c3 - b.c3,
    width: 200,
    align: 'center'
  },
  {
    dataIndex: 'c4',
    title: <div><span>Eigenvector</span><br /><span>Centrality</span></div>,
    sorter: (a, b) => a.c3 - b.c3,
    width: 200,
    align: 'center'
  },
];

class TopPeople extends React.Component {
  render () {
    const {subgraph_info, centrality_data=[]} = this.props;
    // const {centrality_data} = this.props;
    return (
      <div>
        <Divider orientation="left">
          <h3>Subgraph Info</h3>
        </Divider>
        <Descriptions title="Subgraph Info">
          <Descriptions.Item label={`#Node`}>
            {`${subgraph_info.node_num}`}
          </Descriptions.Item>
          <Descriptions.Item label="#Positive tie">
          {`${subgraph_info.pos_tie_num}`}
          </Descriptions.Item>
          <Descriptions.Item label="#Negative tie">
            {`${subgraph_info.neg_tie_num}`}
          </Descriptions.Item>
        </Descriptions>
        <Divider orientation="left">
          <h3>Centrality of Given People</h3>
        </Divider>
        <Table
          columns={columns}
          dataSource={centrality_data}
          size="small"
          pagination={false}
          scroll={{ x: 1050}}
        />
      </div>
    );
  }
}

export default TopPeople;
